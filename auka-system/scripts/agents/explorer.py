"""
AUKA-EXPLORADOR: Agente de descubrimiento de oportunidades comerciales.
Modelo: Kimi K2.5 (principal), Qwen/Gemma (backup)
Principio: Solo descubre fuentes, NO extrae datos.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

from scripts.utils.llm_client import LLMClient
from scripts.utils.validators import validate_json_output

# Intentar cargar la base de conocimiento
KNOWLEDGE_BASE = ""
try:
    kb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs", "knowledge_base.txt")
    if os.path.exists(kb_path):
        with open(kb_path, "r", encoding="utf-8") as f:
            KNOWLEDGE_BASE = f.read()
except Exception as e:
    pass

logger = logging.getLogger("auka.explorador")


class ExplorerAgent:
    """
    Agente Explorador: Genera queries y descubre fuentes de prospectos.
    NO scrapea directamente - propone dónde buscar.
    """
    
    QUERIES_BASE = {
        "empresas": {
            "caracas": [
                "productoras de eventos caracas",
                "organizadores de eventos caracas",
                "salones de eventos caracas",
                "agencias de eventos caracas",
                "productoras audiovisuales caracas"
            ],
            "valencia": [
                "productoras de eventos valencia carabobo",
                "organizadores de eventos valencia",
                "salones de eventos valencia venezuela"
            ],
            "maracay": [
                "productoras de eventos maracay aragua",
                "eventos maracay",
                "salones de eventos maracay"
            ],
            "la_guaira": [
                "eventos la guaira venezuela",
                "productoras de eventos la guaira"
            ]
        },
        "eventos": {
            "deportivos": [
                "eventos deportivos {{ciudad}} 2026",
                "maratón {{ciudad}}",
                "torneo deportivo {{ciudad}}",
                "crossfit evento {{ciudad}}"
            ],
            "corporativos": [
                "ferias empresariales {{ciudad}} 2026",
                "congreso {{ciudad}} venezuela",
                "expo {{ciudad}} 2026",
                "eventos corporativos {{ciudad}}"
            ],
            "culturales": [
                "conciertos {{ciudad}} 2026",
                "festival {{ciudad}} venezuela"
            ]
        },
        "hashtags": {
            "caracas": ["#eventoscaracas", "#caracaseventos", "#eventosvenezuela"],
            "valencia": ["#eventosvalencia", "#valenciaeventos"],
            "maracay": ["#maracayeventos"],
            "la_guaira": ["#laguairaeventos"]
        }
    }
    
    SYSTEM_PROMPT = """
    Eres AUKA-EXPLORADOR, agente especializado en descubrir oportunidades comerciales.
    
    CONTEXTO:
    - Empresa: Aguas Arauka (agua embotellada premium)
    - Cliente ideal: empresas que organizan eventos con 50+ personas
    - Ubicaciones: Caracas, Valencia, Maracay, La Guaira
    
    REGLAS:
    1. NO extraigas datos en profundidad
    2. SOLO descubre fuentes y genera queries optimizadas
    3. Prioriza Google Maps e Instagram
    4. Genera múltiples queries variadas
    5. SIEMPRE devuelve JSON válido
    6. NO inventes empresas ni eventos
    """
    
    def __init__(self):
        self.llm = LLMClient(primary_model="nvidia-kimi-k26", backup_model="llama-3.1-70b")
        if KNOWLEDGE_BASE:
            self.SYSTEM_PROMPT += f"\n\nBASE DE CONOCIMIENTO DE LA EMPRESA:\n{KNOWLEDGE_BASE}"
    
    async def generate_queries(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generar queries optimizadas basadas en el objetivo.
        
        Args:
            input_data: dict con objective, location, context, memory
            
        Returns:
            dict con thought, queries, sources, next_actions
        """
        objective = input_data.get("objective", "eventos")
        location = input_data.get("location", "caracas").lower()
        event_type = input_data.get("event_type", None)
        memory = input_data.get("memory", {})
        
        logger.info(f"[EXPLORADOR] Generando queries: {objective} en {location}")
        
        # Obtener queries base
        base_queries = self._get_base_queries(location, event_type)
        
        # Enriquecer con LLM
        enhanced_queries = await self._enhance_queries_with_llm(
            objective, location, event_type, base_queries, memory
        )
        
        # Combinar y deduplicar
        all_queries = self._merge_and_deduplicate(base_queries, enhanced_queries)
        
        # Seleccionar fuentes
        sources = self._select_sources(location, memory)
        
        # Generar próximas acciones
        next_actions = self._generate_next_actions(all_queries, sources, location)
        
        return {
            "thought": f"Generando {len(all_queries)} queries para {objective} en {location}",
            "queries": all_queries,
            "sources": sources,
            "expansion_strategy": self._determine_strategy(objective),
            "next_actions": next_actions,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "location": location,
                "objective": objective,
                "query_count": len(all_queries)
            }
        }
    
    def _get_base_queries(self, location: str, event_type: Optional[str]) -> List[str]:
        """Obtener queries base según ubicación y tipo."""
        queries = []
        
        if location in self.QUERIES_BASE["empresas"]:
            queries.extend(self.QUERIES_BASE["empresas"][location])
        
        if event_type and event_type in self.QUERIES_BASE["eventos"]:
            templates = self.QUERIES_BASE["eventos"][event_type]
            queries.extend([t.replace("{{ciudad}}", location) for t in templates])
        else:
            for tipo, templates in self.QUERIES_BASE["eventos"].items():
                queries.extend([t.replace("{{ciudad}}", location) for t in templates])
        
        if location in self.QUERIES_BASE["hashtags"]:
            queries.extend(self.QUERIES_BASE["hashtags"][location])
        
        return queries
    
    async def _enhance_queries_with_llm(
        self, objective: str, location: str, event_type: Optional[str],
        base_queries: List[str], memory: Dict
    ) -> List[str]:
        """Usar LLM para generar queries creativas."""
        
        best_queries = memory.get("best_queries", [])
        best_str = "\n".join([f"- {q['query']}" for q in best_queries[:5]]) if best_queries else "Sin datos"
        
        prompt = f"""
        Genera 5 queries creativas para encontrar {objective} en {location}.
        
        Queries base (NO repetir):
        {chr(10).join(f"- {q}" for q in base_queries[:5])}
        
        Mejores queries históricas:
        {best_str}
        
        Requisitos:
        1. Queries variadas, no sinónimos
        2. Términos en español
        3. Variantes regionales venezolanas
        
        Responde SOLO con una lista, una por línea.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt=self.SYSTEM_PROMPT)
            enhanced = [q.strip().lstrip('- ') for q in response.strip().split('\n') 
                       if q.strip() and not q.strip().startswith('-') or q.strip()]
            enhanced = [q for q in enhanced if q]
            return enhanced[:8]
        except Exception as e:
            logger.warning(f"[EXPLORADOR] Falló enriquecimiento LLM: {e}")
            return []
    
    def _merge_and_deduplicate(self, base: List[str], enhanced: List[str]) -> List[str]:
        """Combinar y deduplicar queries."""
        seen = set()
        result = []
        for q in base + enhanced:
            normalized = q.lower().strip()
            if normalized not in seen and len(normalized) > 3:
                seen.add(normalized)
                result.append(q)
        return result[:15]
    
    def _select_sources(self, location: str, memory: Dict) -> List[Dict]:
        """Seleccionar fuentes basadas en rendimiento histórico."""
        fuentes_rendimiento = memory.get("fuentes_rendimiento", {})
        
        sources = []
        for source_type in ["google_maps", "instagram", "web"]:
            eff = fuentes_rendimiento.get(source_type, 0.5)
            priority = "high" if eff > 0.7 else ("low" if eff < 0.3 else "medium")
            sources.append({
                "type": source_type,
                "priority": priority,
                "historical_efficiency": eff
            })
        
        sources.sort(key=lambda x: 0 if x["priority"] == "high" else (1 if x["priority"] == "medium" else 2))
        return sources
    
    def _determine_strategy(self, objective: str) -> str:
        """Determinar estrategia de expansión."""
        if "evento" in objective.lower():
            return "instagram → evento → organizador → empresa"
        elif "empresa" in objective.lower():
            return "maps → empresa → web → instagram → evento"
        return "google → web → empresa → redes"
    
    def _generate_next_actions(self, queries: List[str], sources: List[Dict], location: str) -> List[Dict]:
        """Generar acciones para el Scraper."""
        actions = []
        high_sources = [s for s in sources if s["priority"] == "high"]
        
        for source in high_sources:
            if source["type"] == "google_maps":
                actions.append({
                    "agent": "scraper",
                    "task": "search_maps",
                    "params": {
                        "queries": [q for q in queries if not q.startswith('#')][:5],
                        "location": location,
                        "limit": 20
                    }
                })
            elif source["type"] == "instagram":
                hashtags = [q for q in queries if q.startswith('#')]
                if hashtags:
                    actions.append({
                        "agent": "scraper",
                        "task": "search_instagram",
                        "params": {"hashtags": hashtags[:3], "location": location, "limit": 15}
                    })
        
        return actions


# Instancia singleton
explorer_agent = ExplorerAgent()
