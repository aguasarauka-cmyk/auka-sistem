"""
AUKA-DIRECTOR: Orquestador central del sistema de prospección.
Modelo: Kimi K2.5 (principal), Gemma 4B (fallback)
Principio: Nunca ejecuta directamente, solo delega.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from scripts.utils.llm_client import LLMClient
from scripts.utils.validators import validate_json_output
from config.settings import settings

logger = logging.getLogger("auka.director")


class DirectorAgent:
    """
    Agente Director: Coordina todo el ecosistema de agentes.
    Pipeline interno: ENTENDER → CLASIFICAR → PLANIFICAR → DELEGAR → VALIDAR
    """
    
    AVAILABLE_AGENTS = [
        "explorador",
        "scraper",
        "estructurador",
        "analista",
        "memoria",
        "conversacional"
    ]
    
    SYSTEM_PROMPT = """
    Eres AUKA-DIRECTOR, el agente principal de un sistema autónomo de prospección comercial para Aguas Arauka.

    CONTEXTO DEL NEGOCIO:
    - Producto: Aguas Arauka (agua embotellada premium)
    - Cliente ideal: empresas que organizan eventos con 50+ personas
    - Ciudades objetivo: Caracas, Valencia, Maracay, La Guaira
    - Eventos prioritarios: corporativos, deportivos, ferias, conciertos

    REGLAS OBLIGATORIAS:
    1. NO ejecutes tareas directamente - SIEMPRE delega a otros agentes
    2. SIEMPRE responde en formato JSON válido
    3. NO inventes datos ni empresas
    4. PRIORIZA acciones que generen prospectos con contacto directo
    5. CONSULTA a Memoria antes de iniciar búsquedas para evitar duplicados
    6. SI un agente falla, reintenta con fuente alternativa
    7. NUNCA devuelvas texto libre - solo JSON estructurado

    MODO DE PROSPECCIÓN:
    - MODO_EMPRESAS: Buscar datos de empresas organizadoras de eventos (datos de contacto, web, redes, etc.).
    - MODO_EVENTOS: Buscar eventos específicos que se realizarán en fechas determinadas (nombre del evento, fecha, lugar, organizador, contacto).
    - El agente DEBE preguntar/confirmar el modo antes de iniciar la búsqueda si no está claro en la instrucción del usuario.

    AGENTES DISPONIBLES:
    - explorador: Genera queries y descubre fuentes
    - scraper: Ejecuta scripts de scraping (NO tiene LLM)
    - estructurador: Convierte datos crudos en JSON limpio
    - analista: Evalúa calidad y asigna score
    - memoria: Gestiona duplicados y contexto histórico
    - conversacional: Interfaz con usuario

    FLUJO CORRECTO:
    usuario → ENTENDER → CLASIFICAR → PLANIFICAR → DELEGAR → VALIDAR

    Tu objetivo: maximizar cantidad y calidad de prospectos para Aguas Arauka.
    """
    
    def __init__(self):
        self.llm = LLMClient(primary_model="nvidia-kimi-k26", backup_model="llama-3.1-70b")
        self.session_log: List[Dict] = []
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pipeline principal del Director: 5 fases.
        
        Fases:
            1. ENTENDER: Parsear input
            2. CLASIFICAR: Determinar tipo y prioridad
            3. PLANIFICAR: Secuencia óptima
            4. DELEGAR: Generar actions
            5. VALIDAR: Revisar coherencia
        """
        logger.info(f"[DIRECTOR] Input: {input_data.get('content', '')[:100]}")
        
        # ── FASE 1: ENTENDER ──────────────────────────────────────────
        understood = self._understand(input_data)
        
        # ── FASE 2: CLASIFICAR ────────────────────────────────────────
        classification = self._classify(understood)
        
        # ── FASE 3: PLANIFICAR ────────────────────────────────────────
        plan = self._plan(understood, classification, input_data.get("memory", {}))
        
        # ── FASE 4: DELEGAR ───────────────────────────────────────────
        actions = self._delegate(plan, classification)
        
        # ── FASE 5: VALIDAR ───────────────────────────────────────────
        validated = self._validate(actions, plan)
        
        self._log_session(input_data, validated)
        
        logger.info(f"[DIRECTOR] Decision: {validated['decision']}")
        return validated
    
    def _understand(self, input_data: Dict) -> Dict:
        """Fase 1: Extraer intención, entidades, fuentes y contexto."""
        content = input_data.get("content", "")
        
        prompt = f"""
        Analiza el mensaje y extrae en JSON:
        - intencion_principal: buscar/consultar/analizar/actualizar/resumen/estrategia
        - entidades: {{"ciudad": "...", "tipo_evento": "...", "empresa": "..."}}
        - fuente_preferida: "google_maps", "instagram", "web", o "todas" (infiere según contexto)
        - url: "url específica si el usuario pide analizar un enlace" (null si no hay)
        - modo_prospeccion: "MODO_EMPRESAS" o "MODO_EVENTOS" (infiere según contexto)
        - urgencia: alta/media/baja
        
        Mensaje: "{content}"
        Responde SOLO JSON.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt=self.SYSTEM_PROMPT)
            parsed = validate_json_output(response, default={})
        except Exception as e:
            logger.warning(f"[DIRECTOR] Error entendiendo: {e}")
            parsed = {"intencion_principal": "desconocida", "entidades": {}, "urgencia": "media", "modo_prospeccion": None}
        
        # Fallback determinístico: extraer URL con regex si el LLM no la detectó
        import re
        detected_url = parsed.get("url")
        if not detected_url:
            url_match = re.search(r'https?://[^\s]+', content)
            if url_match:
                detected_url = url_match.group(0)
                logger.info(f"[DIRECTOR] URL detectada por regex: {detected_url}")
        
        # Inferir fuente preferida según la URL
        fuente = parsed.get("fuente_preferida", "todas")
        if detected_url:
            if "instagram.com" in detected_url:
                fuente = "instagram"
            elif "google.com/maps" in detected_url:
                fuente = "google_maps"
            else:
                fuente = "web"
        
        return {
            "original_input": input_data,
            "intention": parsed.get("intencion_principal", "desconocida"),
            "entities": parsed.get("entidades", {}),
            "fuente_preferida": fuente,
            "url": detected_url,
            "modo_prospeccion": parsed.get("modo_prospeccion"),
            "urgency": parsed.get("urgencia", "media"),
            "type": input_data.get("type", "user")
        }
    
    def _classify(self, understood: Dict) -> Dict:
        """Fase 2: Clasificar tarea y asignar prioridad."""
        intention = understood["intention"].lower()
        entities = understood.get("entities", {})
        modo_prospeccion = understood.get("modo_prospeccion")
        
        intention_map = {
            "buscar": {"type": "search", "agent": "explorador", "priority": "high"},
            "encontrar": {"type": "search", "agent": "explorador", "priority": "high"},
            "rastrear": {"type": "search", "agent": "explorador", "priority": "high"},
            "verificar": {"type": "search", "agent": "explorador", "priority": "high"},
            "escanear": {"type": "search", "agent": "explorador", "priority": "high"},
            "extraer": {"type": "search", "agent": "explorador", "priority": "high"},
            "scrape": {"type": "search", "agent": "scraper", "priority": "high"},
            "analizar": {"type": "analyze", "agent": "analista", "priority": "medium"},
            "evaluar": {"type": "analyze", "agent": "analista", "priority": "medium"},
            "consultar": {"type": "query", "agent": "conversacional", "priority": "high"},
            "mostrar": {"type": "query", "agent": "conversacional", "priority": "high"},
            "dame": {"type": "query", "agent": "conversacional", "priority": "high"},
            "resumen": {"type": "report", "agent": "conversacional", "priority": "low"},
            "estadisticas": {"type": "report", "agent": "conversacional", "priority": "low"},
            "estrategia": {"type": "query", "agent": "conversacional", "priority": "medium"},
            "actualizar": {"type": "update", "agent": "conversacional", "priority": "medium"},
            "marcar": {"type": "update", "agent": "conversacional", "priority": "medium"},
        }
        
        classification = intention_map.get(intention, {
            "type": "unknown",
            "agent": "conversacional",
            "priority": "low"
        })
        
        # OVERRIDE: Si hay una URL, SIEMPRE es una búsqueda/scrape, sin importar la intención parseada
        if understood.get("url"):
            classification = {"type": "search", "agent": "scraper", "priority": "high"}
        
        # Subir prioridad si ciudad de alta prioridad
        city = (entities.get("ciudad") or "").lower()
        if city in ["caracas", "valencia"] and classification["priority"] != "high":
            classification["priority"] = "medium"
        
        # Añadir modo de prospección a la clasificación
        classification["modo_prospeccion"] = modo_prospeccion
        
        return classification
    
    def _plan(self, understood: Dict, classification: Dict, memory: Dict) -> Dict:
        """Fase 3: Crear plan de ejecución óptimo."""
        task_type = classification["type"]
        entities = understood.get("entities", {})
        modo_prospeccion = classification.get("modo_prospeccion")
        
        plans = {
            "search": {
                "description": "Pipeline de búsqueda completa",
                "steps": [
                    {"agent": "memoria", "task": "get_context", "reason": "evitar duplicados"},
                    {"agent": "explorador", "task": "generate_queries", "reason": "generar estrategia"},
                    {"agent": "scraper", "task": "execute_search", "reason": "obtener datos crudos"},
                    {"agent": "estructurador", "task": "structure_data", "reason": "limpiar y estructurar"},
                    {"agent": "analista", "task": "evaluate_batch", "reason": "evaluar calidad"},
                    {"agent": "memoria", "task": "save_results", "reason": "persistir y aprender"}
                ]
            },
            "analyze": {
                "description": "Análisis de prospecto existente",
                "steps": [
                    {"agent": "memoria", "task": "get_company", "reason": "recuperar datos"},
                    {"agent": "analista", "task": "evaluate", "reason": "evaluar prospecto"}
                ]
            },
            "query": {
                "description": "Consulta directa a base de datos",
                "steps": [
                    {"agent": "conversacional", "task": "query_db", "reason": "responder al usuario"}
                ]
            },
            "report": {
                "description": "Generación de reporte",
                "steps": [
                    {"agent": "memoria", "task": "get_stats", "reason": "obtener estadísticas"},
                    {"agent": "conversacional", "task": "format_report", "reason": "formatear respuesta"}
                ]
            },
            "update": {
                "description": "Actualización de estado",
                "steps": [
                    {"agent": "conversacional", "task": "update_record", "reason": "actualizar DB"}
                ]
            }
        }
        
        selected_plan = plans.get(task_type, plans["query"])
        
        return {
            "task_type": task_type,
            "description": selected_plan["description"],
            "steps": selected_plan["steps"],
            "entities": entities,
            "fuente_preferida": understood.get("fuente_preferida", "todas"),
            "url": understood.get("url"),
            "modo_prospeccion": modo_prospeccion,
            "estimated_duration": self._estimate_duration(selected_plan["steps"])
        }
    
    def _delegate(self, plan: Dict, classification: Dict) -> List[Dict]:
        """Fase 4: Generar actions JSON para cada paso con enrutamiento dinámico."""
        actions = []
        entities = plan.get("entities", {})
        
        # Extraemos la metadata de enrutamiento previamente parseada
        fuente = plan.get("fuente_preferida", "todas")
        url = plan.get("url")
        modo_prospeccion = plan.get("modo_prospeccion")

        for step in plan["steps"]:
            # ACTUALIZACIÓN: Enrutamiento dinámico de la herramienta Scraper
            if step["agent"] == "scraper" and step["task"] == "execute_search":
                if url:
                    step["task"] = "scrape_web"
                elif fuente == "instagram":
                    step["task"] = "search_instagram"
                elif fuente == "google_maps":
                    step["task"] = "search_maps"
                
                # Añadir modo de prospección a los parámetros del scraper
                step["modo_prospeccion"] = modo_prospeccion

            action = {
                "agent": step["agent"],
                "task": step["task"],
                "params": self._build_params(step, plan), # Se pasa el plan completo para contexto
                "priority": classification["priority"],
                "depends_on": actions[-1]["agent"] if actions else None,
                "reason": step.get("reason", "")
            }
            actions.append(action)
        return actions
    
    def _validate(self, actions: List[Dict], plan: Dict) -> Dict:
        """Fase 5: Validar coherencia del plan."""
        # Asegurar memoria al inicio para búsquedas
        if plan["task_type"] == "search" and (not actions or actions[0]["agent"] != "memoria"):
            actions.insert(0, {
                "agent": "memoria",
                "task": "get_context",
                "params": {},
                "priority": "high",
                "depends_on": None,
                "reason": "evitar duplicados (auto-insertado)"
            })
        
        agents_sequence = [a["agent"] for a in actions]
        priorities = [a["priority"] for a in actions]
        global_priority = "high" if "high" in priorities else ("medium" if "medium" in priorities else "low")
        
        return {
            "thought": f"Plan: {plan['description']}. Secuencia: {' → '.join(agents_sequence)}",
            "decision": f"Ejecutar pipeline de {plan['task_type']}",
            "actions": actions,
            "priority": global_priority,
            "estimated_time_seconds": plan.get("estimated_duration", 180)
        }
    
    def _build_params(self, step: Dict, plan: Dict) -> Dict:
        """Construir parámetros adaptados a la herramienta seleccionada."""
        agent = step["agent"]
        task = step["task"]
        entities = plan.get("entities", {})
        modo_prospeccion = plan.get("modo_prospeccion", "MODO_EMPRESAS")
        
        params = {}
        
        if agent == "explorador" and task == "generate_queries":
            params = {
                "objective": entities.get("intencion", "eventos"),
                "location": entities.get("ciudad", "caracas"),
                "event_type": entities.get("tipo_evento", None),
                "modo_prospeccion": modo_prospeccion
            }
        elif agent == "scraper":
            if task == "scrape_web":
                return {"urls": [plan.get("url")], "modo_prospeccion": modo_prospeccion}
            elif task == "search_instagram":
                return {"hashtags": [entities.get("tipo_evento", "eventos")], "limit": 15, "modo_prospeccion": modo_prospeccion}
            elif task == "search_maps":
                return {
                    "queries": [entities.get("tipo_evento", "eventos")],
                    "location": entities.get("ciudad", "caracas"),
                    "limit": 20,
                    "modo_prospeccion": modo_prospeccion
                }
            elif task == "execute_search":
                return {
                    "queries": [entities.get("tipo_evento", "eventos")],
                    "sources": ["google_maps", "instagram"],
                    "location": entities.get("ciudad", "caracas"),
                    "limit": 20,
                    "modo_prospeccion": modo_prospeccion
                }
        elif agent == "estructurador":
            params = {"source": "auto", "raw_data": {}, "modo_prospeccion": modo_prospeccion}
        elif agent == "analista":
            params = {"prospectos": [], "modo_prospeccion": modo_prospeccion}
        elif agent == "memoria":
            if task == "get_context":
                params = {"scope": "last_24h"}
            elif task == "save_results":
                params = {"results": [], "modo_prospeccion": modo_prospeccion}
        
        return params
    
    def _estimate_duration(self, steps: List[Dict]) -> int:
        """Estimar duración en segundos."""
        base_times = {
            "memoria": 2, "explorador": 5, "scraper": 60,
            "estructurador": 15, "analista": 10, "conversacional": 3
        }
        return sum(base_times.get(step["agent"], 5) for step in steps)
    
    def _log_session(self, input_data: Dict, result: Dict):
        """Registrar en log de sesión."""
        self.session_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "input_type": input_data.get("type"),
            "input_preview": input_data.get("content", "")[:50],
            "decision": result["decision"],
            "actions_count": len(result["actions"]),
            "priority": result["priority"]
        })


# Instancia singleton
director_agent = DirectorAgent()
