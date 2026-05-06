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
        """Fase 1: Extraer intención, entidades y contexto."""
        content = input_data.get("content", "")
        
        prompt = f"""
        Analiza el mensaje y extrae en JSON:
        - intencion_principal: qué quiere el usuario (buscar/consultar/analizar/actualizar/resumen)
        - entidades: {{"ciudad": "...", "tipo_evento": "...", "empresa": "..."}}
        - urgencia: alta/media/baja
        
        Mensaje: "{content}"
        Responde SOLO JSON.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt=self.SYSTEM_PROMPT)
            parsed = validate_json_output(response, default={
                "intencion_principal": "desconocida",
                "entidades": {},
                "urgencia": "media"
            })
        except Exception as e:
            logger.warning(f"[DIRECTOR] Error entendiendo: {e}")
            parsed = {"intencion_principal": "desconocida", "entidades": {}, "urgencia": "media"}
        
        return {
            "original_input": input_data,
            "intention": parsed.get("intencion_principal", "desconocida"),
            "entities": parsed.get("entidades", {}),
            "urgency": parsed.get("urgencia", "media"),
            "type": input_data.get("type", "user")
        }
    
    def _classify(self, understood: Dict) -> Dict:
        """Fase 2: Clasificar tarea y asignar prioridad."""
        intention = understood["intention"].lower()
        entities = understood.get("entities", {})
        
        intention_map = {
            "buscar": {"type": "search", "agent": "explorador", "priority": "high"},
            "encontrar": {"type": "search", "agent": "explorador", "priority": "high"},
            "rastrear": {"type": "search", "agent": "explorador", "priority": "high"},
            "analizar": {"type": "analyze", "agent": "analista", "priority": "medium"},
            "evaluar": {"type": "analyze", "agent": "analista", "priority": "medium"},
            "consultar": {"type": "query", "agent": "conversacional", "priority": "high"},
            "mostrar": {"type": "query", "agent": "conversacional", "priority": "high"},
            "dame": {"type": "query", "agent": "conversacional", "priority": "high"},
            "resumen": {"type": "report", "agent": "conversacional", "priority": "low"},
            "estadisticas": {"type": "report", "agent": "conversacional", "priority": "low"},
            "actualizar": {"type": "update", "agent": "conversacional", "priority": "medium"},
            "marcar": {"type": "update", "agent": "conversacional", "priority": "medium"},
        }
        
        classification = intention_map.get(intention, {
            "type": "unknown",
            "agent": "conversacional",
            "priority": "low"
        })
        
        # Subir prioridad si ciudad de alta prioridad
        city = (entities.get("ciudad") or "").lower()
        if city in ["caracas", "valencia"] and classification["priority"] != "high":
            classification["priority"] = "medium"
        
        return classification
    
    def _plan(self, understood: Dict, classification: Dict, memory: Dict) -> Dict:
        """Fase 3: Crear plan de ejecución óptimo."""
        task_type = classification["type"]
        entities = understood.get("entities", {})
        
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
            "estimated_duration": self._estimate_duration(selected_plan["steps"])
        }
    
    def _delegate(self, plan: Dict, classification: Dict) -> List[Dict]:
        """Fase 4: Generar actions JSON para cada paso."""
        actions = []
        entities = plan.get("entities", {})
        
        for step in plan["steps"]:
            action = {
                "agent": step["agent"],
                "task": step["task"],
                "params": self._build_params(step, entities),
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
    
    def _build_params(self, step: Dict, entities: Dict) -> Dict:
        """Construir parámetros para cada tipo de tarea."""
        agent = step["agent"]
        task = step["task"]
        params = {}
        
        if agent == "explorador" and task == "generate_queries":
            params = {
                "objective": entities.get("intencion", "eventos"),
                "location": entities.get("ciudad", "caracas"),
                "event_type": entities.get("tipo_evento", None)
            }
        elif agent == "scraper" and task == "execute_search":
            params = {
                "queries": [],
                "sources": ["google_maps", "instagram"],
                "limit": 20,
                "location": entities.get("ciudad", "caracas")
            }
        elif agent == "estructurador":
            params = {"source": "auto", "raw_data": {}}
        elif agent == "analista":
            params = {"prospectos": []}
        elif agent == "memoria":
            if task == "get_context":
                params = {"scope": "last_24h"}
            elif task == "save_results":
                params = {"results": []}
        
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
