# AUKA - Sistema Autónomo de Prospección B2B
## Documentación Técnica Completa - Nivel Producción

**Empresa:** Aguas Arauka  
**Versión:** 2.0 Profesional  
**Fecha:** 2026-05-06  
**Autor:** Sistema de Agentes Autónomos

---

## TABLA DE CONTENIDO

1. [Arquitectura del Sistema](#1-arquitectura-del-sistema)
2. [Notas de Corrección y Mejoras](#2-notas-de-corrección-y-mejoras-respecto-a-v10)
3. [Estructura del Proyecto](#3-estructura-del-proyecto)
4. [Agente Director (AUKA-DIRECTOR)](#4-agente-director-aukadirector)
5. [Agente Explorador (AUKA-EXPLORADOR)](#5-agente-explorador-aukaexplorador)
6. [Agente Scraper (AUKA-SCRAPER)](#6-agente-scraper-aukascraper)
7. [Agente Estructurador (AUKA-ESTRUCTURADOR)](#7-agente-estructurador-aukaestructurador)
8. [Agente Analista (AUKA-ANALISTA)](#8-agente-analista-aukaanalista)
9. [Agente Memoria (AUKA-MEMORIA)](#9-agente-memoria-aukamemoria)
10. [Agente Conversacional (AUKA-CONVERSACIONAL)](#10-agente-conversacional-aukaconversacional)
11. [Integración Dashboard](#11-integración-dashboard)
12. [Flujo Completo de Datos](#12-flujo-completo-de-datos)
13. [Configuración y Despliegue](#13-configuración-y-despliegue)

---

## 1. ARQUITECTURA DEL SISTEMA

### 1.1 Diagrama de Agentes

```
                    ┌─────────────────────────┐
                    │    USUARIO (Telegram/    │
                    │       Dashboard)         │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │   AUKA-CONVERSACIONAL   │  ◄── Interfaz humana
                    │   (Kimi K2.5)           │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │     AUKA-DIRECTOR       │  ◄── Orquestador central
                    │     (Kimi K2.5)         │
                    └──────┬────────┬─────────┘
                           │        │
              ┌────────────┘        └────────────┐
              │                                   │
    ┌─────────▼──────────┐            ┌───────────▼──────────┐
    │  AUKA-EXPLORADOR   │            │   AUKA-MEMORIA       │
    │  (Kimi K2.5)       │            │   (Lógica + DB)      │
    └─────────┬──────────┘            └───────────┬──────────┘
              │                                   │
    ┌─────────▼──────────┐            ┌───────────▼──────────┐
    │   AUKA-SCRAPER     │            │   SUPABASE (PostgreSQL)│
    │   (Python Scripts) │            │                      │
    └─────────┬──────────┘            └──────────────────────┘
              │
    ┌─────────▼──────────┐
    │ AUKA-ESTRUCTURADOR │  ◄── Conversión datos crudos → JSON
    │ (Gemma 4B / Kimi)  │
    └─────────┬──────────┘
              │
    ┌─────────▼──────────┐
    │   AUKA-ANALISTA    │  ◄── Scoring + Priorización
    │   (Kimi K2.5)      │
    └────────────────────┘
```

### 1.2 Pipeline de Procesamiento

```
[Input] → [Director] → [Explorador] → [Scraper] → [Estructurador] → [Analista] → [Memoria] → [Supabase]
   ↑                                                                                        │
   └──────────────────────────── [Conversacional] ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←─┘
```

### 1.3 Modelos Asignados

| Agente | Modelo Principal | Modelo Backup | Razón |
|--------|-----------------|---------------|-------|
| Director | Kimi K2.5 | Gemma 4B | Planificación, razonamiento |
| Explorador | Kimi K2.5 | Qwen / Gemma | Creatividad en queries |
| Scraper | Sin LLM | - | Ejecución pura de scripts |
| Estructurador | Gemma 4B | Kimi K2.5 | Velocidad en extracción |
| Analista | Kimi K2.5 | DeepSeek | Razonamiento de negocio |
| Conversacional | Kimi K2.5 | - | NLP, comprensión contextual |
| Memoria | Lógica determinística | - | Velocidad, sin alucinación |

### 1.4 Fuentes de Datos

| Fuente | Prioridad | Datos Extraídos | Estrategia Anti-Bloqueo |
|--------|-----------|-----------------|------------------------|
| Google Maps | ALTA | Empresa, teléfono, dirección, web, coordenadas | Scroll progresivo, rotación de queries |
| Instagram | ALTA | Bio, posts, captions, teléfonos, eventos | Delays aleatorios, sesión persistente, rotación UA |
| Web (Playwright) | MEDIA | HTML completo, eventos, emails ocultos | User-agent real, timeouts |

### 1.5 Geografía Objetivo

- **Caracas** (Distrito Capital) - Prioridad máxima
- **Valencia** (Carabobo) - Prioridad alta
- **Maracay** (Aragua) - Prioridad alta
- **La Guaira** (Vargas) - Prioridad media

---

## 2. NOTAS DE CORRECCIÓN Y MEJORAS RESPECTO A V1.0

### 2.1 Correcciones Críticas

| # | Problema en V1.0 | Corrección V2.0 |
|---|-----------------|-----------------|
| 1 | El Orquestador ejecutaba scraping directamente | Orquestador **solo delega**, nunca ejecuta |
| 2 | Un solo agente "todoterreno" | **7 agentes especializados** con responsabilidad única |
| 3 | Modelo NVIDIA Kimi K2.5 no existe | Corrección: **Kimi K2.5** (Moonshot AI) |
| 4 | Sin sistema anti-duplicados | Agente **Memoria** con deduplicación hash + fuzzy |
| 5 | Sin control de calidad de datos | Agente **Analista** con scoring 0-100 |
| 6 | Sin memoria de búsquedas previas | Tablas `memoria_busquedas`, `memoria_empresas` |
| 7 | Bot Telegram sin clasificación de intenciones | Clasificador LLM de 6 categorías de intención |
| 8 | Sin reporte de eficiencia del sistema | Reporte automático por fuente y query |

### 2.2 Mejoras Arquitectónicas

1. **Formato JSON obligatorio** en todos los agentes → previene "alucinaciones" de texto libre
2. **Pipeline de 5 fases**: Entender → Clasificar → Planificar → Delegar → Validar
3. **Sistema de confianza** (alta/media/baja) en Estructurador
4. **Scoring determinista** sin LLM en Analista (más rápido)
5. **Caché local** en Memoria para últimas 100 empresas
6. **Contexto conversacional** de últimas 5 interacciones

### 2.3 Mejoras de Robustez

1. **Anti-alucinación estricta**: null en vez de "desconocido", solo datos confirmados
2. **Fallback automático**: si falla scraping → cambiar fuente; si falla modelo → usar backup
3. **Control de velocidad**: delays aleatorios 1.5-4s en scraping
4. **Timeout de 10s** por extracción LLM
5. **Validación de JSON** antes de procesar

---

## 3. ESTRUCTURA DEL PROYECTO

```
auka-system/
├── config/
│   ├── __init__.py
│   ├── settings.py              # Variables de entorno y configuración
│   ├── models_config.yaml       # Configuración de modelos LLM
│   └── sources.yaml             # Fuentes de datos y queries base
│
├── scripts/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── director.py          # AUKA-DIRECTOR
│   │   ├── explorer.py          # AUKA-EXPLORADOR
│   │   ├── scraper.py           # AUKA-SCRAPER (router)
│   │   ├── structurer.py        # AUKA-ESTRUCTURADOR
│   │   ├── analyst.py           # AUKA-ANALISTA
│   │   ├── memory.py            # AUKA-MEMORIA
│   │   └── conversational.py    # AUKA-CONVERSACIONAL
│   │
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── google_maps.py       # Scraper de Google Maps
│   │   ├── instagram.py         # Scraper de Instagram
│   │   └── web_playwright.py    # Scraper genérico web
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── llm_client.py        # Cliente unificado de LLMs
│   │   ├── validators.py        # Validadores de JSON y datos
│   │   ├── cleaners.py          # Limpieza de texto/HTML
│   │   └── logger.py            # Sistema de logging
│   │
│   └── database/
│       ├── __init__.py
│       ├── supabase_client.py   # Cliente de Supabase
│       └── schemas.py           # Esquemas de tablas SQL
│
├── bot/
│   ├── __init__.py
│   └── telegram_bot.py          # Bot de Telegram
│
├── dashboard/
│   └── (Next.js - ver documento aparte)
│
├── tests/
│   ├── test_director.py
│   ├── test_explorer.py
│   ├── test_scraper.py
│   ├── test_structurer.py
│   ├── test_analyst.py
│   ├── test_memory.py
│   └── test_conversational.py
│
├── docs/
│   └── SISTEMA_AUKA_DOCUMENTACION_TECNICA_COMPLETA.md
│
├── .env.example
├── requirements.txt
└── main.py                      # Punto de entrada del sistema
```

---

## 4. AGENTE DIRECTOR (AUKA-DIRECTOR)

### 4.1 Especificación

| Atributo | Valor |
|----------|-------|
| Nombre | AUKA-DIRECTOR |
| Tipo | Orquestador central / Coordinador multi-agente |
| Modelo | Kimi K2.5 (principal), Gemma 4B (fallback simplificado) |
| Rol | Tomar decisiones estratégicas y coordinar todo el sistema |

### 4.2 Responsabilidades

- Interpretar instrucciones del usuario (vía Conversacional)
- Planificar secuencia de tareas
- Delegar a agentes especializados (nunca ejecutar directamente)
- Controlar flujo de ejecución
- Validar resultados intermedios
- Evitar redundancias (consultando a Memoria)
- Priorizar acciones por impacto comercial
- Gestionar errores y reintentos

### 4.3 Input / Output Estándar

**INPUT:**
```json
{
  "type": "user | system | agent",
  "content": "mensaje o resultado de otro agente",
  "context": {
    "session_id": "uuid",
    "user_id": "12345",
    "previous_actions": []
  },
  "memory": {
    "queries_realizadas": [],
    "empresas_vistas": [],
    "ciudades_cubiertas": []
  }
}
```

**OUTPUT (JSON obligatorio):**
```json
{
  "thought": "Análisis interno del Director sobre la situación",
  "decision": "descripción de la decisión tomada",
  "actions": [
    {
      "agent": "explorador | scraper | estructurador | analista | memoria | conversacional",
      "task": "nombre_de_tarea",
      "params": {},
      "priority": "high | medium | low",
      "depends_on": null
    }
  ],
  "priority": "high | medium | low",
  "estimated_time_seconds": 180
}
```

### 4.4 Sistema de Pensamiento (5 Fases)

```
[INPUT] → [1. ENTENDER] → [2. CLASIFICAR] → [3. PLANIFICAR] → [4. DELEGAR] → [5. VALIDAR] → [OUTPUT]
```

| Fase | Descripción | Ejemplo |
|------|-------------|---------|
| ENTENDER | Parsear el input y extraer intención | "buscar eventos deportivos en Caracas" → objetivo: eventos deportivos, ubicación: Caracas |
| CLASIFICAR | Determinar tipo de tarea y prioridad | Tipo: exploración, Prioridad: high (nueva oportunidad) |
| PLANIFICAR | Definir secuencia óptima de agentes | 1. Consultar Memoria → 2. Explorador genera queries → 3. Scraper ejecuta → 4. Estructurador limpia → 5. Analista evalúa |
| DELEGAR | Generar actions JSON para cada agente | [{"agent": "memoria", "task": "get_context"}, {"agent": "explorador", "task": "generate_queries"}] |
| VALIDAR | Revisar resultados y decidir si continuar o ajustar | Si resultados < esperado → refinamiento; si duplicados → ignorar |

### 4.5 Motor de Decisiones

**Clasificación de Intención:**

| Input Pattern | Tipo | Agente Destino | Prioridad |
|--------------|------|----------------|-----------|
| "buscar/eventos/encontrar" | Búsqueda | Explorador → Scraper | HIGH |
| "analizar/evaluar/score" | Análisis | Analista | MEDIUM |
| "consultar/dame/muestra" | Consulta DB | Conversacional (DB) | HIGH |
| "estado/resumen/stats" | Reporte | Conversacional (Stats) | LOW |
| "contactar/marcar/actualizar" | Acción CRM | Conversacional (Update) | MEDIUM |

**Prioridades Automáticas:**
- **HIGH**: Nuevas oportunidades, consultas de alta prioridad
- **MEDIUM**: Enriquecimiento de datos existentes
- **LOW**: Reportes, limpieza, mantenimiento

### 4.6 Prompt Base (Sistema Anti-Alucinación)

```python
SYSTEM_PROMPT_DIRECTOR = """
Eres AUKA-DIRECTOR, el agente principal de un sistema autónomo de prospección comercial para Aguas Arauka.

CONTEXTO DEL NEGOCIO:
- Producto: Aguas Arauka (agua embotellada premium)
- Cliente ideal: empresas que organizan eventos con 50+ personas
- Ciudades objetivo: Caracas, Valencia, Maracay, La Guaira
- Eventos prioritarios: corporativos, deportivos, ferias, conciertos

REGLAS OBLIGATORIAS:
1. NO ejecutes tareas directamente - SIEMPRE delega a otros agentes
2. SIEMPPE responde en formato JSON válido
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
```

### 4.7 Código del Agente Director

```python
# scripts/agents/director.py
"""
AUKA-DIRECTOR: Orquestador central del sistema de prospección.
Modelo: Kimi K2.5 (principal), Gemma 4B (fallback)
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from scripts.utils.llm_client import LLMClient
from scripts.utils.validators import validate_json_output
from scripts.database.supabase_client import SupabaseClient

logger = logging.getLogger("auka.director")


class DirectorAgent:
    """
    Agente Director: Coordina todo el ecosistema de agentes.
    Principio: Nunca ejecuta directamente, solo delega.
    """
    
    AVAILABLE_AGENTS = [
        "explorador",
        "scraper", 
        "estructurador",
        "analista",
        "memoria",
        "conversacional"
    ]
    
    PRIORITY_WEIGHTS = {
        "high": 3,
        "medium": 2,
        "low": 1
    }
    
    def __init__(self):
        self.llm = LLMClient(primary_model="kimi-k2.5", backup_model="gemma-4b")
        self.db = SupabaseClient()
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
        logger.info(f"[DIRECTOR] Input recibido: {input_data.get('content', '')[:100]}")
        
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
        
        # Log de sesión
        self._log_session(input_data, validated)
        
        logger.info(f"[DIRECTOR] Decisión: {validated['decision']}")
        logger.info(f"[DIRECTOR] Acciones generadas: {len(validated['actions'])}")
        
        return validated
    
    def _understand(self, input_data: Dict) -> Dict:
        """Fase 1: Extraer intención, entidades y contexto del input."""
        content = input_data.get("content", "")
        
        prompt = f"""
        Analiza el siguiente mensaje y extrae:
        - intencion_principal: qué quiere el usuario
        - entidades: empresas, ciudades, tipos de evento mencionados
        - urgencia: alta/media/baja
        
        Mensaje: "{content}"
        
        Responde SOLO con JSON válido.
        """
        
        response = self.llm.generate(prompt, system_prompt=self.SYSTEM_PROMPT_DIRECTOR)
        parsed = validate_json_output(response, default={
            "intencion_principal": "desconocida",
            "entidades": {},
            "urgencia": "media"
        })
        
        return {
            "original_input": input_data,
            "intention": parsed.get("intencion_principal", "desconocida"),
            "entities": parsed.get("entidades", {}),
            "urgency": parsed.get("urgencia", "media"),
            "type": input_data.get("type", "user")
        }
    
    def _classify(self, understood: Dict) -> Dict:
        """Fase 2: Clasificar la tarea y asignar prioridad."""
        intention = understood["intention"].lower()
        entities = understood.get("entities", {})
        
        # Mapa de intenciones → tipo de tarea
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
        
        # Subir prioridad si hay ciudad de alta prioridad
        high_priority_cities = ["caracas", "valencia"]
        city = entities.get("ciudad", "").lower()
        if city in high_priority_cities and classification["priority"] != "high":
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
                    {"agent": "explorador", "task": "generate_queries", "reason": "generar estrategia de búsqueda"},
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
        """Fase 4: Generar actions JSON para cada paso del plan."""
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
        """Fase 5: Validar coherencia del plan generado."""
        # Verificar que no hay ciclos
        agents_sequence = [a["agent"] for a in actions]
        
        # Verificar que conversacional solo está al inicio o final
        conversational_positions = [i for i, a in enumerate(actions) if a["agent"] == "conversacional"]
        
        # Verificar que memoria está al inicio para búsquedas
        if plan["task_type"] == "search" and actions and actions[0]["agent"] != "memoria":
            # Insertar consulta a memoria al inicio
            actions.insert(0, {
                "agent": "memoria",
                "task": "get_context",
                "params": {},
                "priority": "high",
                "depends_on": None,
                "reason": "evitar duplicados (auto-insertado en validación)"
            })
        
        # Calcular prioridad global
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
        """Construir parámetros específicos para cada tipo de tarea."""
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
                "queries": [],  # Se llena dinámicamente del explorador
                "sources": ["google_maps", "instagram"],
                "limit": 20
            }
        elif agent == "estructurador":
            params = {
                "source": "auto",
                "raw_data": {}  # Se llena del scraper
            }
        elif agent == "analista":
            params = {
                "prospectos": []  # Se llena del estructurador
            }
        elif agent == "memoria":
            if task == "get_context":
                params = {"scope": "last_24h"}
            elif task == "save_results":
                params = {"results": []}
        
        return params
    
    def _estimate_duration(self, steps: List[Dict]) -> int:
        """Estimar duración en segundos basado en los pasos."""
        base_times = {
            "memoria": 2,
            "explorador": 5,
            "scraper": 60,
            "estructurador": 15,
            "analista": 10,
            "conversacional": 3
        }
        total = sum(base_times.get(step["agent"], 5) for step in steps)
        return total
    
    def _log_session(self, input_data: Dict, result: Dict):
        """Registrar en log de sesión para trazabilidad."""
        self.session_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "input_type": input_data.get("type"),
            "input_preview": input_data.get("content", "")[:50],
            "decision": result["decision"],
            "actions_count": len(result["actions"]),
            "priority": result["priority"]
        })
    
    def get_session_summary(self) -> Dict:
        """Obtener resumen de la sesión actual."""
        return {
            "total_decisions": len(self.session_log),
            "decisions_by_priority": {
                "high": sum(1 for s in self.session_log if s["priority"] == "high"),
                "medium": sum(1 for s in self.session_log if s["priority"] == "medium"),
                "low": sum(1 for s in self.session_log if s["priority"] == "low")
            },
            "history": self.session_log[-10:]  # Últimas 10
        }


# Instancia singleton
director_agent = DirectorAgent()
```

### 4.8 Integración con otros Agentes

```
Recibe de: Agente Conversacional (instrucciones del usuario)
Envía a:   Explorador (tareas de descubrimiento)
            Scraper (tareas de extracción)
            Estructurador (tareas de procesamiento)
            Analista (tareas de evaluación)
            Memoria (consultas de contexto)
```

---

## 5. AGENTE EXPLORADOR (AUKA-EXPLORADOR)

### 5.1 Especificación

| Atributo | Valor |
|----------|-------|
| Nombre | AUKA-EXPLORADOR |
| Tipo | Descubrimiento / Expansión de fuentes |
| Modelo | Kimi K2.5 (principal), Qwen / Gemma (backup) |
| Rol | Encontrar dónde están los prospectos |

### 5.2 Responsabilidades

- Generar queries inteligentes y variadas
- Descubrir empresas, eventos, perfiles y URLs
- Expandir la búsqueda mediante loops de exploración
- Priorizar fuentes por eficiencia histórica
- NO extraer datos en profundidad (eso es del Scraper)

### 5.3 Input / Output

**INPUT:**
```json
{
  "task": "search | expand | refine",
  "objective": "eventos deportivos",
  "location": "caracas",
  "context": {
    "previous_queries": [],
    "sources_used": []
  },
  "memory": {
    "best_queries": [],
    "cities_covered": []
  }
}
```

**OUTPUT (JSON obligatorio):**
```json
{
  "thought": "Análisis de la estrategia de búsqueda",
  "queries": [
    "eventos deportivos caracas",
    "productoras de eventos deportivos caracas",
    "#eventosdeportivoscaracas"
  ],
  "sources": [
    {"type": "google_maps", "priority": "high", "reason": "datos directos de empresa"},
    {"type": "instagram", "priority": "high", "reason": "eventos activos"}
  ],
  "expansion_strategy": "maps → empresa → web → instagram → evento",
  "next_actions": [
    {"agent": "scraper", "task": "search_maps", "params": {"query": "eventos deportivos caracas"}}
  ]
}
```

### 5.4 Estrategias de Expansión

| Patrón | Descripción | Caso de Uso |
|--------|-------------|-------------|
| Patrón 1: Maps → Empresa → Web → IG → Evento | Encontrar empresa en Maps, visitar web, rastrear Instagram, detectar eventos | Búsqueda inicial |
| Patrón 2: IG → Evento → Organizador → Empresa | Encontrar evento en Instagram, identificar organizador, buscar empresa | Eventos activos |
| Patrón 3: Google → Web → Empresa → Redes | Buscar en Google, encontrar web, extraer empresa y sus redes | Descubrimiento |

### 5.5 Generación de Queries

**Queries Base por Categoría:**

```python
QUERIES_TEMPLATE = {
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
            "productoras de eventos la guaira",
            "organizadores de eventos vargas"
        ]
    },
    "eventos": {
        "deportivos": [
            "eventos deportivos {ciudad} 2026",
            "maratón {ciudad}",
            "torneo deportivo {ciudad}",
            "crossfit evento {ciudad}",
            "feria deportiva {ciudad}"
        ],
        "corporativos": [
            "ferias empresariales {ciudad} 2026",
            "congreso {ciudad}",
            "expo {ciudad} venezuela",
            "eventos corporativos {ciudad}",
            "summit {ciudad}"
        ],
        "culturales": [
            "conciertos {ciudad} 2026",
            "festival {ciudad} venezuela",
            "eventos culturales {ciudad}"
        ],
        "gastronomicos": [
            "food festival {ciudad}",
            "feria gastronomica {ciudad}",
            "eventos gastronomicos {ciudad}"
        ]
    },
    "hashtags": {
        "caracas": ["#eventoscaracas", "#caracaseventos", "#eventosvenezuela"],
        "valencia": ["#eventosvalencia", "#valenciaeventos", "#caraboboeventos"],
        "maracay": ["#maracayeventos", "#eventosaragua", "#araguaeventos"],
        "la_guaira": ["#laguairaeventos", "#eventosvargas", "#eventoslaguaira"]
    }
}
```

### 5.6 Código del Agente Explorador

```python
# scripts/agents/explorer.py
"""
AUKA-EXPLORADOR: Agente de descubrimiento de oportunidades comerciales.
Modelo: Kimi K2.5 (principal), Qwen/Gemma (backup)
Principio: Solo descubre fuentes, NO extrae datos.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from scripts.utils.llm_client import LLMClient
from scripts.utils.validators import validate_json_output

logger = logging.getLogger("auka.explorador")


class ExplorerAgent:
    """
    Agente Explorador: Genera queries y descubre fuentes de prospectos.
    NO scrapea directamente - propone dónde buscar.
    """
    
    # Queries base optimizadas para Venezuela
    QUERIES_BASE = {
        "empresas": {
            "caracas": [
                "productoras de eventos caracas",
                "organizadores de eventos caracas", 
                "salones de eventos caracas",
                "agencias de eventos caracas",
                "productoras audiovisuales caracas",
                "event planners caracas venezuela"
            ],
            "valencia": [
                "productoras de eventos valencia carabobo",
                "organizadores de eventos valencia",
                "salones de eventos valencia venezuela",
                "eventos valencia carabobo 2026"
            ],
            "maracay": [
                "productoras de eventos maracay aragua",
                "eventos maracay",
                "salones de eventos maracay",
                "organizadores de eventos maracay"
            ],
            "la_guaira": [
                "eventos la guaira venezuela",
                "productoras de eventos la guaira",
                "eventos vargas venezuela"
            ]
        },
        "eventos": {
            "deportivos": [
                "eventos deportivos {ciudad} 2026",
                "maratón {ciudad}",
                "torneo deportivo {ciudad}",
                "crossfit evento {ciudad}",
                "carrera {ciudad} 2026",
                "fitness festival {ciudad}"
            ],
            "corporativos": [
                "ferias empresariales {ciudad} 2026",
                "congreso {ciudad} venezuela",
                "expo {ciudad} 2026",
                "eventos corporativos {ciudad}",
                "summit {ciudad}",
                "conferencia {ciudad} 2026"
            ],
            "culturales": [
                "conciertos {ciudad} 2026",
                "festival {ciudad} venezuela",
                "eventos culturales {ciudad}",
                "teatro {ciudad} eventos"
            ],
            "sociales": [
                "eventos sociales {ciudad}",
                "bodas y quinceañeras {ciudad}",
                "fiestas corporativas {ciudad}"
            ]
        },
        "hashtags": {
            "caracas": ["#eventoscaracas", "#caracaseventos", "#eventosvenezuela", "#eventoscaracas2026"],
            "valencia": ["#eventosvalencia", "#valenciaeventos", "#caraboboeventos", "#eventosvalencia2026"],
            "maracay": ["#maracayeventos", "#eventosaragua", "#araguaeventos"],
            "la_guaira": ["#laguairaeventos", "#eventosvargas", "#eventoslaguaira"]
        }
    }
    
    SOURCES_PRIORITY = {
        "google_maps": {"priority": "high", "reason": "datos directos de empresa"},
        "instagram": {"priority": "high", "reason": "eventos activos y contactos"},
        "web": {"priority": "medium", "reason": "información detallada"},
        "google_search": {"priority": "medium", "reason": "descubrimiento amplio"}
    }
    
    SYSTEM_PROMPT = """
    Eres AUKA-EXPLORADOR, un agente especializado en descubrir oportunidades comerciales.
    
    CONTEXTO:
    - Empresa: Aguas Arauka (agua embotellada premium)
    - Cliente ideal: empresas que organizan eventos con 50+ personas
    - Ubicaciones: Caracas, Valencia, Maracay, La Guaira
    
    REGLAS OBLIGATORIAS:
    1. NO extraigas datos en profundidad - eso lo hace el Scraper
    2. SOLO descubre fuentes y genera queries optimizadas
    3. Prioriza Google Maps e Instagram
    4. Genera múltiples queries variadas (evita repetición)
    5. SIEMPRE devuelve JSON válido
    6. NO inventes empresas ni eventos
    7. Piensa en cómo expandir la búsqueda (loops)
    
    ESTRATEGIA DE EXPANSIÓN:
    - Patrón 1: Maps → Empresa → Web → Instagram → Evento
    - Patrón 2: Instagram → Evento → Organizador → Empresa nueva
    - Patrón 3: Google → Web → Empresa → Redes sociales
    """
    
    def __init__(self):
        self.llm = LLMClient(primary_model="kimi-k2.5", backup_model="qwen")
    
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
        
        logger.info(f"[EXPLORADOR] Generando queries para: {objective} en {location}")
        
        # Obtener queries base
        base_queries = self._get_base_queries(location, event_type)
        
        # Enriquecer con LLM para queries creativas
        enhanced_queries = await self._enhance_queries_with_llm(
            objective, location, event_type, base_queries, memory
        )
        
        # Deduplicar y mezclar
        all_queries = self._merge_and_deduplicate(base_queries, enhanced_queries)
        
        # Seleccionar fuentes óptimas
        sources = self._select_sources(location, memory)
        
        # Generar próximas acciones
        next_actions = self._generate_next_actions(all_queries, sources, location)
        
        result = {
            "thought": f"Generando {len(all_queries)} queries para {objective} en {location}. "
                      f"Fuentes priorizadas: {', '.join(s['type'] for s in sources)}",
            "queries": all_queries,
            "sources": sources,
            "expansion_strategy": self._determine_strategy(objective, location),
            "next_actions": next_actions,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "location": location,
                "objective": objective,
                "query_count": len(all_queries)
            }
        }
        
        logger.info(f"[EXPLORADOR] {len(all_queries)} queries generadas")
        return result
    
    def _get_base_queries(self, location: str, event_type: Optional[str]) -> List[str]:
        """Obtener queries base según ubicación y tipo."""
        queries = []
        
        # Queries de empresas para la ciudad
        if location in self.QUERIES_BASE["empresas"]:
            queries.extend(self.QUERIES_BASE["empresas"][location])
        
        # Queries de eventos
        if event_type and event_type in self.QUERIES_BASE["eventos"]:
            templates = self.QUERIES_BASE["eventos"][event_type]
            queries.extend([q.format(ciudad=location) for q in templates])
        else:
            # Incluir todos los tipos
            for tipo, templates in self.QUERIES_BASE["eventos"].items():
                queries.extend([q.format(ciudad=location) for q in templates])
        
        # Hashtags relevantes
        if location in self.QUERIES_BASE["hashtags"]:
            queries.extend(self.QUERIES_BASE["hashtags"][location])
        
        return queries
    
    async def _enhance_queries_with_llm(
        self, 
        objective: str, 
        location: str, 
        event_type: Optional[str],
        base_queries: List[str],
        memory: Dict
    ) -> List[str]:
        """Usar LLM para generar queries creativas y específicas."""
        
        best_queries = memory.get("best_queries", [])
        best_queries_str = "\n".join([f"- {q['query']} (eficiencia: {q.get('eficiencia', 'N/A')})" 
                                       for q in best_queries[:5]]) if best_queries else "Sin datos históricos"
        
        prompt = f"""
        Genera 5 queries de búsqueda creativas y específicas para encontrar {objective} en {location}.
        
        Contexto:
        - Empresa: Aguas Arauka (agua embotellada premium)
        - Buscamos: empresas organizadoras de eventos con 50+ personas
        - Ciudades clave: Caracas, Valencia, Maracay, La Guaira
        
        Queries base ya generadas (NO repetir):
        {chr(10).join(f"- {q}" for q in base_queries[:5])}
        
        Queries históricas con mejor rendimiento:
        {best_queries_str}
        
        Requisitos:
        1. Queries variadas (no sinónimos de las base)
        2. Incluye términos en español
        3. Considera variantes regionales venezolanas
        4. Algunas queries específicas de nicho
        
        Responde SOLO con una lista de queries, una por línea.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt=self.SYSTEM_PROMPT)
            # Parsear respuesta: una query por línea
            enhanced = [q.strip() for q in response.strip().split('\n') 
                       if q.strip() and not q.strip().startswith('-')]
            enhanced = [q.lstrip('- ').strip() for q in enhanced]
            return enhanced[:8]  # Máximo 8 adicionales
        except Exception as e:
            logger.warning(f"[EXPLORADOR] Falló enriquecimiento LLM: {e}")
            return []
    
    def _merge_and_deduplicate(
        self, 
        base: List[str], 
        enhanced: List[str]
    ) -> List[str]:
        """Combinar y deduplicar queries manteniendo orden de prioridad."""
        seen = set()
        result = []
        
        for q in base + enhanced:
            normalized = q.lower().strip()
            if normalized not in seen and len(normalized) > 3:
                seen.add(normalized)
                result.append(q)
        
        return result[:15]  # Máximo 15 queries por búsqueda
    
    def _select_sources(self, location: str, memory: Dict) -> List[Dict]:
        """Seleccionar fuentes basadas en prioridad y rendimiento histórico."""
        sources = []
        
        # Verificar rendimiento histórico de fuentes
        fuentes_rendimiento = memory.get("fuentes_rendimiento", {})
        
        for source_type, config in self.SOURCES_PRIORITY.items():
            # Ajustar prioridad si hay datos históricos
            eff = fuentes_rendimiento.get(source_type, 0.5)
            priority = config["priority"]
            if eff > 0.7:
                priority = "high"
            elif eff < 0.3:
                priority = "low"
            
            sources.append({
                "type": source_type,
                "priority": priority,
                "reason": config["reason"],
                "historical_efficiency": eff
            })
        
        # Ordenar por prioridad
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sources.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return sources
    
    def _determine_strategy(self, objective: str, location: str) -> str:
        """Determinar estrategia de expansión óptima."""
        if "evento" in objective.lower() or "feria" in objective.lower():
            return "instagram → evento → organizador → empresa nueva"
        elif "empresa" in objective.lower() or "productora" in objective.lower():
            return "maps → empresa → web → instagram → evento"
        else:
            return "google → web → empresa → redes sociales"
    
    def _generate_next_actions(
        self, 
        queries: List[str], 
        sources: List[Dict],
        location: str
    ) -> List[Dict]:
        """Generar acciones siguientes para el Scraper."""
        actions = []
        
        # Filtrar fuentes de alta prioridad
        high_priority_sources = [s for s in sources if s["priority"] == "high"]
        
        for source in high_priority_sources:
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
                        "params": {
                            "hashtags": hashtags[:3],
                            "location": location,
                            "limit": 15
                        }
                    })
            elif source["type"] == "web":
                actions.append({
                    "agent": "scraper",
                    "task": "search_web",
                    "params": {
                        "queries": queries[:3],
                        "location": location
                    }
                })
        
        return actions


# Instancia singleton
explorer_agent = ExplorerAgent()
```

---

## 6. AGENTE SCRAPER (AUKA-SCRAPER)

### 6.1 Especificación

| Atributo | Valor |
|----------|-------|
| Nombre | AUKA-SCRAPER |
| Tipo | Ejecutor técnico / Recolector de datos |
| Modelo | Sin LLM (Python puro) |
| Rol | Extraer datos reales desde la web |

### 6.2 Responsabilidades

- Ejecutar scripts de scraping especializados
- Navegar páginas web (JavaScript dinámico)
- Extraer datos crudos sin interpretación
- Manejar sesiones (login Instagram)
- Controlar delays y evitar bloqueos
- Retornar datos estructurables (NO datos finales)

### 6.3 Principio Clave

> El Scraper **NO piensa como humano**. Ejecuta, recolecta, devuelve. No analiza, no interpreta, no decide estrategia.

### 6.4 Router de Tareas

```
INPUT → Validación → Selector de Scraper → Ejecución → Normalización → Return JSON
```

| Task | Scraper | Output |
|------|---------|--------|
| search_maps | Google Maps Scraper | Lista de empresas con datos básicos |
| scrape_instagram | Instagram Scraper | Perfil + posts recientes |
| scrape_web | Playwright Web Scraper | HTML completo de página |

### 6.5 Código del Agente Scraper

```python
# scripts/agents/scraper.py
"""
AUKA-SCRAPER: Router de scraping. Delega a scrapers especializados.
NO usa LLM. Ejecución pura de Python.
Principio: Ejecuta, recolecta, devuelve. No interpreta.
"""

import json
import logging
import time
import random
from typing import Dict, List, Optional, Any

from scripts.scrapers.google_maps import GoogleMapsScraper
from scripts.scrapers.instagram import InstagramScraper
from scripts.scrapers.web_playwright import WebScraper

logger = logging.getLogger("auka.scraper")


class ScraperAgent:
    """
    Agente Scraper: Router que ejecuta scraping según la fuente.
    NO tiene lógica de negocio - solo orquesta scrapers técnicos.
    """
    
    def __init__(self):
        self.maps_scraper = GoogleMapsScraper()
        self.ig_scraper = InstagramScraper()
        self.web_scraper = WebScraper()
        
        # Control de velocidad global
        self.min_delay = 1.5
        self.max_delay = 4.0
    
    async def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecutar tarea de scraping según el tipo.
        
        Args:
            task_data: dict con task, params
            
        Returns:
            dict con status, data, meta
        """
        task = task_data.get("task", "")
        params = task_data.get("params", {})
        
        logger.info(f"[SCRAPER] Ejecutando tarea: {task}")
        
        # Router de tareas
        if task == "search_maps":
            result = await self._execute_maps_search(params)
        elif task == "scrape_instagram":
            result = await self._execute_instagram(params)
        elif task == "scrape_web" or task == "search_web":
            result = await self._execute_web(params)
        elif task == "execute_search":
            # Tarea compuesta: ejecutar múltiples búsquedas
            result = await self._execute_composite_search(params)
        else:
            result = {
                "status": "error",
                "data": None,
                "meta": {"error": f"Tarea '{task}' no soportada"}
            }
        
        # Aplicar delay anti-bloqueo
        self._apply_delay()
        
        logger.info(f"[SCRAPER] Tarea {task} completada: {result.get('meta', {}).get('count', 0)} resultados")
        return result
    
    async def _execute_maps_search(self, params: Dict) -> Dict:
        """Ejecutar búsqueda en Google Maps."""
        queries = params.get("queries", [])
        location = params.get("location", "")
        limit = params.get("limit", 20)
        
        all_results = []
        errors = []
        
        for query in queries:
            try:
                results = await self.maps_scraper.search(
                    query=f"{query} {location}".strip(),
                    limit=limit
                )
                all_results.extend(results)
                
                # Delay entre queries
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"[SCRAPER] Error en Maps query '{query}': {e}")
                errors.append({"query": query, "error": str(e)})
        
        # Normalizar resultados
        normalized = [self._normalize_maps_result(r) for r in all_results]
        
        return {
            "status": "success" if normalized else "partial_error",
            "data": normalized,
            "meta": {
                "source": "google_maps",
                "count": len(normalized),
                "queries_executed": len(queries),
                "errors": errors if errors else None
            }
        }
    
    async def _execute_instagram(self, params: Dict) -> Dict:
        """Ejecutar scraping de Instagram."""
        hashtags = params.get("hashtags", [])
        profiles = params.get("profiles", [])
        limit = params.get("limit", 15)
        
        all_results = []
        errors = []
        
        # Buscar por hashtags
        for hashtag in hashtags:
            try:
                results = await self.ig_scraper.search_by_hashtag(
                    hashtag=hashtag,
                    limit=limit
                )
                all_results.extend(results)
                time.sleep(random.uniform(3, 6))
            except Exception as e:
                logger.error(f"[SCRAPER] Error en IG hashtag '{hashtag}': {e}")
                errors.append({"hashtag": hashtag, "error": str(e)})
        
        # Scrapear perfiles si se proporcionan
        for profile in profiles:
            try:
                result = await self.ig_scraper.scrape_profile(profile)
                all_results.append(result)
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                logger.error(f"[SCRAPER] Error en IG profile '{profile}': {e}")
                errors.append({"profile": profile, "error": str(e)})
        
        normalized = [self._normalize_instagram_result(r) for r in all_results]
        
        return {
            "status": "success" if normalized else "partial_error",
            "data": normalized,
            "meta": {
                "source": "instagram",
                "count": len(normalized),
                "hashtags_searched": hashtags,
                "profiles_scraped": profiles,
                "errors": errors if errors else None
            }
        }
    
    async def _execute_web(self, params: Dict) -> Dict:
        """Ejecutar scraping web con Playwright."""
        urls = params.get("urls", [])
        queries = params.get("queries", [])
        
        all_results = []
        errors = []
        
        # Scrapear URLs directas
        for url in urls:
            try:
                result = await self.web_scraper.scrape(url)
                all_results.append(result)
                time.sleep(random.uniform(1.5, 3))
            except Exception as e:
                logger.error(f"[SCRAPER] Error en web scrape '{url}': {e}")
                errors.append({"url": url, "error": str(e)})
        
        # Si hay queries, buscar y luego scrapear
        if queries and not urls:
            # Aquí se integraría con búsqueda Google
            pass
        
        normalized = [self._normalize_web_result(r) for r in all_results]
        
        return {
            "status": "success" if normalized else "partial_error",
            "data": normalized,
            "meta": {
                "source": "web",
                "count": len(normalized),
                "urls_scraped": len(urls),
                "errors": errors if errors else None
            }
        }
    
    async def _execute_composite_search(self, params: Dict) -> Dict:
        """Ejecutar búsqueda compuesta en múltiples fuentes."""
        queries = params.get("queries", [])
        sources = params.get("sources", ["google_maps", "instagram"])
        location = params.get("location", "")
        limit = params.get("limit", 20)
        
        all_results = []
        
        if "google_maps" in sources:
            maps_result = await self._execute_maps_search({
                "queries": queries,
                "location": location,
                "limit": limit
            })
            if maps_result["status"] == "success":
                all_results.extend(maps_result["data"])
        
        if "instagram" in sources:
            hashtags = [q for q in queries if q.startswith('#')]
            if hashtags:
                ig_result = await self._execute_instagram({
                    "hashtags": hashtags,
                    "limit": limit
                })
                if ig_result["status"] == "success":
                    all_results.extend(ig_result["data"])
        
        return {
            "status": "success",
            "data": all_results,
            "meta": {
                "source": "composite",
                "count": len(all_results),
                "sources_used": sources
            }
        }
    
    def _normalize_maps_result(self, raw: Dict) -> Dict:
        """Normalizar resultado de Google Maps a formato estándar."""
        return {
            "source": "google_maps",
            "empresa": raw.get("title") or raw.get("name"),
            "direccion": raw.get("address"),
            "telefono": raw.get("phone"),
            "web": raw.get("website"),
            "rating": raw.get("rating"),
            "reviews": raw.get("reviews"),
            "coordenadas": {
                "lat": raw.get("latitude"),
                "lng": raw.get("longitude")
            },
            "ciudad": self._extract_city_from_address(raw.get("address", "")),
            "raw_data": raw
        }
    
    def _normalize_instagram_result(self, raw: Dict) -> Dict:
        """Normalizar resultado de Instagram a formato estándar."""
        return {
            "source": "instagram",
            "empresa": raw.get("full_name") or raw.get("username"),
            "instagram": f"@{raw.get('username', '')}",
            "bio": raw.get("biography"),
            "telefono": raw.get("contact_phone_number") or self._extract_phone_from_bio(raw.get("biography", "")),
            "email": raw.get("public_email") or self._extract_email_from_bio(raw.get("biography", "")),
            "web": raw.get("external_url"),
            "posts": raw.get("posts", []),
            "seguidores": raw.get("follower_count"),
            "raw_data": raw
        }
    
    def _normalize_web_result(self, raw: Dict) -> Dict:
        """Normalizar resultado web a formato estándar."""
        return {
            "source": "web",
            "url": raw.get("url"),
            "html": raw.get("html"),
            "titulo": raw.get("title"),
            "meta_description": raw.get("meta_description"),
            "raw_data": raw
        }
    
    def _extract_city_from_address(self, address: str) -> Optional[str]:
        """Extraer ciudad de una dirección venezolana."""
        if not address:
            return None
        
        cities = ["caracas", "valencia", "maracay", "la guaira", "barquisimeto", 
                  "maturín", "puerto la cruz", "san cristobal"]
        address_lower = address.lower()
        
        for city in cities:
            if city in address_lower:
                return city.title()
        
        return None
    
    def _extract_phone_from_bio(self, bio: str) -> Optional[str]:
        """Extraer teléfono de una bio de Instagram."""
        import re
        if not bio:
            return None
        
        # Patrones de teléfono venezolano
        patterns = [
            r'\+?58[-\s]?\d{3}[-\s]?\d{7}',
            r'0\d{3}[-\s]?\d{7}',
            r'\d{4}[-\s]?\d{7}'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, bio)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_email_from_bio(self, bio: str) -> Optional[str]:
        """Extraer email de una bio de Instagram."""
        import re
        if not bio:
            return None
        
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(pattern, bio)
        return match.group(0) if match else None
    
    def _apply_delay(self):
        """Aplicar delay aleatorio anti-bloqueo."""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)


# Instancia singleton
scraper_agent = ScraperAgent()
```

### 6.6 Scraper Google Maps (Detalle)

```python
# scripts/scrapers/google_maps.py
"""
Google Maps Scraper: Extrae empresas desde búsquedas de Google Maps.
Técnica: Playwright con scroll infinito.
Anti-bloqueo: Delays progresivos, user-agent real.
"""

import asyncio
import logging
from typing import List, Dict, Optional
from playwright.async_api import async_playwright

logger = logging.getLogger("auka.scraper.maps")


class GoogleMapsScraper:
    """Scraper especializado para Google Maps."""
    
    BASE_URL = "https://www.google.com/maps/search/"
    
    async def search(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Buscar empresas en Google Maps.
        
        Args:
            query: término de búsqueda
            limit: máximo de resultados
            
        Returns:
            Lista de dicts con datos de empresas
        """
        results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                # Navegar a Google Maps con la query
                search_url = f"{self.BASE_URL}{query.replace(' ', '+')}"
                await page.goto(search_url, wait_until="networkidle")
                
                # Esperar carga de resultados
                await page.wait_for_selector('[jstcache="3"]', timeout=10000)
                
                # Scroll progresivo para cargar más resultados
                scroll_count = 0
                max_scrolls = min(limit // 5 + 1, 10)
                
                while scroll_count < max_scrolls:
                    # Extraer resultados visibles
                    cards = await page.query_selector_all('[jstcache="3"]')
                    
                    for card in cards[len(results):]:
                        if len(results) >= limit:
                            break
                        
                        try:
                            data = await self._extract_card_data(card)
                            if data and data not in results:
                                results.append(data)
                        except Exception as e:
                            logger.debug(f"Error extrayendo card: {e}")
                    
                    if len(results) >= limit:
                        break
                    
                    # Scroll down
                    await page.evaluate("window.scrollBy(0, 800)")
                    await asyncio.sleep(2)
                    scroll_count += 1
                
            except Exception as e:
                logger.error(f"Error en Maps search: {e}")
            finally:
                await browser.close()
        
        return results[:limit]
    
    async def _extract_card_data(self, card) -> Optional[Dict]:
        """Extraer datos de una tarjeta de resultado."""
        try:
            title = await card.query_selector_eval("h3", "el => el.textContent")
            address = await card.query_selector_eval(
                "[data-result-index] ~ div", 
                "el => el.textContent"
            )
            
            return {
                "title": title.strip() if title else None,
                "address": address.strip() if address else None,
                "source": "google_maps"
            }
        except Exception:
            return None
```

---

## 7. AGENTE ESTRUCTURADOR (AUKA-ESTRUCTURADOR)

### 7.1 Especificación

| Atributo | Valor |
|----------|-------|
| Nombre | AUKA-ESTRUCTURADOR |
| Tipo | Procesador semántico / Extractor de entidades |
| Modelo | Gemma 4B (principal), Kimi K2.5 (textos complejos) |
| Rol | Convertir datos crudos en información estructurada |

### 7.2 Responsabilidades

- Recibir datos crudos del Scraper (HTML, texto, captions)
- Limpiar y normalizar información
- Extraer entidades clave (empresa, evento, fecha, contacto)
- Clasificar tipo de evento
- Detectar si hay datos suficientes para guardar
- Devolver JSON estructurado válido

### 7.3 Pipeline Interno

```
[Datos Crudos] → [Limpieza] → [Extracción LLM] → [Clasificación] → [Evaluación] → [JSON Válido]
```

### 7.4 Clasificación de Tipos de Evento

| Categoría | Ejemplos | Keywords |
|-----------|----------|----------|
| deportivo | maratón, torneo, fitness, fútbol, CrossFit | maratón, carrera, torneo, fitness, deporte |
| corporativo | congreso, feria, expo, conferencia, summit | congreso, feria, expo, conferencia, summit, corporativo |
| social | boda, quinceañera, grado, fiesta privada | boda, quinceañera, graduación, fiesta |
| cultural | concierto, festival, teatro, arte | concierto, festival, teatro, arte, cultural |
| gastronómico | food festival, degustación, mercado | gastronomía, food, degustación, culinary |
| religioso | retiro, misa especial, culto masivo | retiro, iglesia, religioso, culto |
| otro | sin clasificación clara | - |

### 7.5 Sistema de Confianza

| Nivel | Condición | Acción |
|-------|-----------|--------|
| ALTA | empresa + evento + contacto presentes | Guardar directamente |
| MEDIA | empresa + ciudad presentes | Guardar con flag 'enriquecer' |
| BAJA | datos insuficientes | Descartar o enviar a enriquecimiento |

### 7.6 Código del Agente Estructurador

```python
# scripts/agents/structurer.py
"""
AUKA-ESTRUCTURADOR: Convierte datos crudos en JSON estructurado.
Modelo: Gemma 4B (principal), Kimi K2.5 (textos complejos > 1000 palabras)
Principio: Solo transforma, no busca información adicional.
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from scripts.utils.llm_client import LLMClient
from scripts.utils.validators import validate_json_output
from scripts.utils.cleaners import TextCleaner

logger = logging.getLogger("auka.estructurador")


class StructurerAgent:
    """
    Agente Estructurador: Extrae información comercial de texto crudo.
    Output: JSON estandarizado para el Analista.
    """
    
    SYSTEM_PROMPT = """
    Eres AUKA-ESTRUCTURADOR, un agente especializado en extraer información comercial 
    estructurada a partir de texto crudo para la prospección de Aguas Arauka.
    
    REGLAS OBLIGATORIAS:
    1. NUNCA inventes datos que no estén en el texto
    2. Si un campo no existe, devuelve null (NO "desconocido")
    3. SIEMPRE devuelve JSON válido
    4. Extrae SOLO lo que puedas confirmar del texto
    5. Evalúa la confianza: alta/media/baja
    
    CATEGORÍAS DE EVENTO:
    - deportivo: maratón, torneo, fitness, fútbol, CrossFit
    - corporativo: congreso, feria, expo, conferencia, summit
    - social: boda, quinceañera, grado, fiesta privada
    - cultural: concierto, festival, teatro, arte
    - gastronomico: food festival, degustación, mercado
    - religioso: retiro, misa especial, culto masivo
    - otro: sin clasificación clara
    
    CONFIDENCIA:
    - alta: empresa + evento + contacto presentes
    - media: empresa + ciudad presentes
    - baja: datos insuficientes
    
    Devuelve SOLO el JSON, sin texto adicional.
    """
    
    # Campos esperados en el output
    OUTPUT_FIELDS = [
        "empresa", "evento", "tipo_evento", "fecha", "ubicacion",
        "ciudad", "telefono", "email", "instagram", "web",
        "confianza", "completo"
    ]
    
    def __init__(self):
        self.llm = LLMClient(primary_model="gemma-4b", backup_model="kimi-k2.5")
        self.cleaner = TextCleaner()
    
    async def structure(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estructurar datos crudos en JSON limpio.
        
        Args:
            input_data: dict con source, raw_data
            
        Returns:
            dict con datos estructurados y metadata
        """
        source = input_data.get("source", "unknown")
        raw_data = input_data.get("raw_data", {})
        
        logger.info(f"[ESTRUCTURADOR] Procesando datos de: {source}")
        
        # ── 1. LIMPIAR ──────────────────────────────────────────────
        cleaned_text = self._clean_raw_data(raw_data, source)
        
        # ── 2. EXTRAER CON LLM ──────────────────────────────────────
        extracted = await self._extract_with_llm(cleaned_text, source)
        
        # ── 3. VALIDAR Y COMPLETAR ──────────────────────────────────
        validated = self._validate_output(extracted)
        
        # ── 4. DETERMINAR ACCIÓN ────────────────────────────────────
        action = self._determine_action(validated)
        
        result = {
            **validated,
            "_metadata": {
                "source": source,
                "processed_at": datetime.utcnow().isoformat(),
                "action": action,
                "raw_text_length": len(cleaned_text)
            }
        }
        
        logger.info(f"[ESTRUCTURADOR] Procesado: confianza={result.get('confianza')}, "
                    f"completo={result.get('completo')}, acción={action}")
        
        return result
    
    def _clean_raw_data(self, raw_data: Dict, source: str) -> str:
        """Limpiar datos crudos según la fuente."""
        if source == "google_maps":
            text = raw_data.get("text", "")
            # Extraer campos ya estructurados de Maps
            parts = []
            if raw_data.get("empresa"):
                parts.append(f"Empresa: {raw_data['empresa']}")
            if raw_data.get("direccion"):
                parts.append(f"Dirección: {raw_data['direccion']}")
            if raw_data.get("telefono"):
                parts.append(f"Teléfono: {raw_data['telefono']}")
            if raw_data.get("web"):
                parts.append(f"Web: {raw_data['web']}")
            text = " | ".join(parts) if parts else text
            
        elif source == "instagram":
            # Combinar bio y captions
            parts = []
            if raw_data.get("bio"):
                parts.append(raw_data["bio"])
            posts = raw_data.get("posts", [])
            for post in posts[:5]:  # Máximo 5 posts
                if isinstance(post, dict) and post.get("caption"):
                    parts.append(post["caption"])
            text = "\n---\n".join(parts)
            
        elif source == "web":
            text = raw_data.get("html", "")
        else:
            text = str(raw_data)
        
        # Aplicar limpieza general
        return self.cleaner.clean(text)
    
    async def _extract_with_llm(self, text: str, source: str) -> Dict:
        """Extraer entidades usando LLM."""
        
        # Seleccionar modelo según longitud del texto
        text_length = len(text)
        if text_length > 1000:
            model = "kimi-k2.5"
            logger.info(f"[ESTRUCTURADOR] Usando Kimi K2.5 para texto largo ({text_length} chars)")
        else:
            model = "gemma-4b"
        
        # Truncar texto si es muy largo
        max_chars = 3000
        text_truncated = text[:max_chars] if len(text) > max_chars else text
        
        prompt = f"""
        Extrae la información comercial del siguiente texto.
        
        Fuente: {source}
        Texto:
        ---
        {text_truncated}
        ---
        
        Extrae y devuelve SOLO un JSON con estos campos:
        {{
            "empresa": "nombre de la empresa organizadora o null",
            "evento": "nombre del evento o null",
            "tipo_evento": "deportivo/corporativo/social/cultural/gastronomico/religioso/otro o null",
            "fecha": "fecha del evento en YYYY-MM-DD o null",
            "ubicacion": "lugar específico o null",
            "ciudad": "ciudad (Caracas/Valencia/Maracay/La Guaira) o null",
            "telefono": "número de contacto o null",
            "email": "correo electrónico o null",
            "instagram": "usuario de Instagram o null",
            "web": "URL del sitio web o null",
            "confianza": "alta/media/baja",
            "completo": true/false
        }}
        
        REGLAS:
        - Si un dato NO está en el texto, usa null
        - NO inventes datos
        - confianza=alta si hay empresa+evento+contacto
        - completo=true si hay empresa+contacto
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt=self.SYSTEM_PROMPT, model=model)
            extracted = validate_json_output(response)
            
            # Asegurar que todos los campos existen
            for field in self.OUTPUT_FIELDS:
                if field not in extracted:
                    extracted[field] = None
            
            return extracted
            
        except Exception as e:
            logger.error(f"[ESTRUCTURADOR] Error en extracción LLM: {e}")
            return self._create_empty_output("extraction_failed")
    
    def _validate_output(self, data: Dict) -> Dict:
        """Validar y corregir el output del LLM."""
        # Normalizar nulls
        for field in self.OUTPUT_FIELDS:
            if field not in data or data[field] in ["", "null", "desconocido", "unknown"]:
                data[field] = None
        
        # Inferir ciudad si no está pero hay ubicación
        if not data.get("ciudad") and data.get("ubicacion"):
            data["ciudad"] = self._infer_city(data["ubicacion"])
        
        # Calcular confianza si no está o es inconsistente
        if data.get("confianza") not in ["alta", "media", "baja"]:
            data["confianza"] = self._calculate_confidence(data)
        
        # Calcular completo si no está
        if not isinstance(data.get("completo"), bool):
            has_empresa = bool(data.get("empresa"))
            has_contacto = bool(data.get("telefono") or data.get("email") or data.get("instagram"))
            data["completo"] = has_empresa and has_contacto
        
        return data
    
    def _determine_action(self, data: Dict) -> str:
        """Determinar acción a tomar según confianza."""
        confianza = data.get("confianza", "baja")
        
        if confianza == "alta":
            return "guardar"
        elif confianza == "media":
            data["estado"] = "enriquecer"
            return "guardar_con_flag"
        else:
            return "descartar"
    
    def _infer_city(self, ubicacion: str) -> Optional[str]:
        """Inferir ciudad desde una ubicación."""
        cities = ["caracas", "valencia", "maracay", "la guaira"]
        ubicacion_lower = ubicacion.lower()
        
        for city in cities:
            if city in ubicacion_lower:
                return city.title()
        
        # Detectar por zona/distrito
        if any(x in ubicacion_lower for x in ["distrito capital", "chacao", "baruta", "el hatillo"]):
            return "Caracas"
        if any(x in ubicacion_lower for x in ["carabobo", "naguanagua", "san diego"]):
            return "Valencia"
        if any(x in ubicacion_lower for x in ["aragua", "girardot"]):
            return "Maracay"
        
        return None
    
    def _calculate_confidence(self, data: Dict) -> str:
        """Calcular nivel de confianza basado en datos presentes."""
        score = 0
        
        if data.get("empresa"): score += 3
        if data.get("evento"): score += 2
        if data.get("telefono"): score += 2
        if data.get("email"): score += 2
        if data.get("instagram"): score += 1
        if data.get("web"): score += 1
        if data.get("ciudad"): score += 1
        if data.get("fecha"): score += 1
        
        if score >= 8: return "alta"
        elif score >= 4: return "media"
        else: return "baja"
    
    def _create_empty_output(self, reason: str) -> Dict:
        """Crear output vacío en caso de error."""
        return {
            "empresa": None,
            "evento": None,
            "tipo_evento": None,
            "fecha": None,
            "ubicacion": None,
            "ciudad": None,
            "telefono": None,
            "email": None,
            "instagram": None,
            "web": None,
            "confianza": "baja",
            "completo": False,
            "_error": reason
        }


# Instancia singleton
structurer_agent = StructurerAgent()
```

---

## 8. AGENTE ANALISTA (AUKA-ANALISTA)

### 8.1 Especificación

| Atributo | Valor |
|----------|-------|
| Nombre | AUKA-ANALISTA |
| Tipo | Evaluador / Clasificador de calidad |
| Modelo | Kimi K2.5 (principal), DeepSeek (backup) |
| Rol | Evaluar calidad comercial de cada prospecto |

### 8.2 Responsabilidades

- Recibir JSON estructurado del Estructurador
- Evaluar completitud de datos
- Calcular score de prospecto (0-100)
- Clasificar prioridad: ALTA / MEDIA / BAJA
- Detectar señales de oportunidad
- Generar recomendación de acción comercial
- Marcar prospectos para enriquecimiento

### 8.3 Sistema de Scoring (Determinista)

| Señal | Puntos | Condición |
|-------|--------|-----------|
| Teléfono directo | +20 | `telefono` presente |
| Evento próximo | +20 | `fecha` dentro de 60 días |
| Activa en Instagram | +15 | `instagram` presente |
| Email de contacto | +15 | `email` presente |
| Página web | +10 | `web` presente |
| Empresa identificada | +10 | `empresa` presente |
| Ciudad prioritaria | +5 | Caracas o Valencia |
| Tipo prioritario | +5 | corporativo o deportivo |

**Rangos de Prioridad:**

| Score | Prioridad | Acción Recomendada |
|-------|-----------|-------------------|
| 80-100 | ALTA | Contactar esta semana |
| 50-79 | MEDIA | Contactar este mes |
| 0-49 | BAJA | Enriquecer antes de contactar |

### 8.4 Código del Agente Analista

```python
# scripts/agents/analyst.py
"""
AUKA-ANALISTA: Evalúa la calidad comercial de prospectos.
Modelo: Kimi K2.5 (solo para recomendación en texto natural)
Scoring: 100% determinista (sin LLM, más rápido)
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from scripts.utils.llm_client import LLMClient

logger = logging.getLogger("auka.analista")


class AnalystAgent:
    """
    Agente Analista: Evalúa prospectos y asigna score de prioridad.
    Scoring determinista + recomendación con LLM.
    """
    
    SYSTEM_PROMPT = """
    Eres AUKA-ANALISTA, un agente especializado en evaluar la calidad comercial 
    de prospectos para Aguas Arauka.
    
    CONTEXTO DEL NEGOCIO:
    - Producto: Aguas Arauka (agua embotellada premium)
    - Cliente ideal: empresas que organizan eventos con 50+ personas
    - Ciudades clave: Caracas, Valencia, Maracay, La Guaira
    - Eventos prioritarios: corporativos, deportivos, ferias
    
    REGLAS:
    1. Evalúa SOLO con los datos que recibes
    2. NO inventes señales positivas
    3. Sé crítico: sin contacto = baja prioridad
    4. SIEMPRE devuelve JSON válido
    5. El score debe reflejar oportunidad REAL de venta
    """
    
    # Tabla de puntuación
    SCORING_RULES = {
        "telefono": {"points": 20, "signal": "tiene teléfono directo"},
        "fecha_proxima": {"points": 20, "signal": "tiene evento próximo (≤60 días)"},
        "email": {"points": 15, "signal": "tiene email de contacto"},
        "instagram": {"points": 15, "signal": "activa en Instagram"},
        "web": {"points": 10, "signal": "tiene página web"},
        "empresa": {"points": 10, "signal": "empresa identificada"},
        "ciudad_top": {"points": 5, "signal": "ciudad de alta prioridad"},
        "tipo_top": {"points": 5, "signal": "tipo de evento prioritario"}
    }
    
    PRIORITY_RANGES = {
        "ALTA": (80, 100, "contactar esta semana"),
        "MEDIA": (50, 79, "contactar este mes"),
        "BAJA": (0, 49, "enriquecer datos antes de contactar")
    }
    
    CITIES_TOP = ["caracas", "valencia", "maracay", "la guaira"]
    EVENT_TYPES_TOP = ["corporativo", "deportivo"]
    
    def __init__(self):
        self.llm = LLMClient(primary_model="kimi-k2.5")
    
    async def evaluate(self, prospecto: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluar un prospecto y generar análisis completo.
        
        Args:
            prospecto: dict con datos estructurados del prospecto
            
        Returns:
            dict con score, prioridad, recomendación, señales
        """
        logger.info(f"[ANALISTA] Evaluando prospecto: {prospecto.get('empresa', 'N/A')}")
        
        # ── 1. CALCULAR SCORE (determinista) ──────────────────────────
        score, pos_signals, neg_signals = self._calculate_score(prospecto)
        
        # ── 2. CLASIFICAR PRIORIDAD ──────────────────────────────────
        prioridad, accion = self._classify_priority(score)
        
        # ── 3. DETECTAR SEÑALES DE OPORTUNIDAD ───────────────────────
        oportunidad = self._detect_opportunity_signals(prospecto)
        
        # ── 4. GENERAR RECOMENDACIÓN (con LLM) ───────────────────────
        recomendacion = await self._generate_recommendation(
            prospecto, score, pos_signals, oportunidad
        )
        
        # ── 5. IDENTIFICAR CAMPOS FALTANTES ──────────────────────────
        campos_faltantes = self._identify_missing_fields(prospecto)
        
        result = {
            "score": score,
            "prioridad": prioridad,
            "accion_recomendada": accion,
            "razon": recomendacion,
            "señales_positivas": pos_signals,
            "señales_negativas": neg_signals,
            "señales_oportunidad": oportunidad,
            "enriquecer": score < 50,
            "campos_faltantes": campos_faltantes,
            "evaluado_en": datetime.utcnow().isoformat()
        }
        
        logger.info(f"[ANALISTA] Score: {score}, Prioridad: {prioridad}")
        
        return result
    
    async def evaluate_batch(self, prospectos: List[Dict]) -> List[Dict]:
        """Evaluar múltiples prospectos en batch."""
        results = []
        for p in prospectos:
            result = await self.evaluate(p)
            results.append({"prospecto": p, "analisis": result})
        return results
    
    def _calculate_score(self, prospecto: Dict) -> Tuple[int, List[str], List[str]]:
        """Calcular score determinista basado en reglas."""
        score = 0
        pos_signals = []
        neg_signals = []
        
        # Teléfono directo (+20)
        if prospecto.get("telefono"):
            score += self.SCORING_RULES["telefono"]["points"]
            pos_signals.append(self.SCORING_RULES["telefono"]["signal"])
        else:
            neg_signals.append("sin teléfono de contacto")
        
        # Evento próximo (+20)
        fecha = prospecto.get("fecha")
        if fecha and self._is_event_soon(fecha):
            score += self.SCORING_RULES["fecha_proxima"]["points"]
            pos_signals.append(self.SCORING_RULES["fecha_proxima"]["signal"])
        elif fecha:
            pos_signals.append("tiene fecha pero evento lejano")
        else:
            neg_signals.append("sin fecha de evento")
        
        # Email (+15)
        if prospecto.get("email"):
            score += self.SCORING_RULES["email"]["points"]
            pos_signals.append(self.SCORING_RULES["email"]["signal"])
        else:
            neg_signals.append("sin email")
        
        # Instagram (+15)
        if prospecto.get("instagram"):
            score += self.SCORING_RULES["instagram"]["points"]
            pos_signals.append(self.SCORING_RULES["instagram"]["signal"])
        
        # Web (+10)
        if prospecto.get("web"):
            score += self.SCORING_RULES["web"]["points"]
            pos_signals.append(self.SCORING_RULES["web"]["signal"])
        
        # Empresa identificada (+10)
        if prospecto.get("empresa"):
            score += self.SCORING_RULES["empresa"]["points"]
            pos_signals.append(self.SCORING_RULES["empresa"]["signal"])
        else:
            neg_signals.append("sin empresa identificada")
        
        # Ciudad prioritaria (+5)
        ciudad = (prospecto.get("ciudad") or "").lower()
        if any(c in ciudad for c in self.CITIES_TOP):
            score += self.SCORING_RULES["ciudad_top"]["points"]
            pos_signals.append(self.SCORING_RULES["ciudad_top"]["signal"])
        
        # Tipo prioritario (+5)
        tipo = (prospecto.get("tipo_evento") or "").lower()
        if tipo in self.EVENT_TYPES_TOP:
            score += self.SCORING_RULES["tipo_top"]["points"]
            pos_signals.append(self.SCORING_RULES["tipo_top"]["signal"])
        
        return min(score, 100), pos_signals, neg_signals
    
    def _classify_priority(self, score: int) -> Tuple[str, str]:
        """Clasificar prioridad basada en score."""
        for prioridad, (min_score, max_score, accion) in self.PRIORITY_RANGES.items():
            if min_score <= score <= max_score:
                return prioridad, accion
        return "BAJA", "enriquecer datos antes de contactar"
    
    def _detect_opportunity_signals(self, prospecto: Dict) -> List[str]:
        """Detectar señales adicionales de oportunidad."""
        signals = []
        
        # Evento muy próximo (< 30 días)
        fecha = prospecto.get("fecha")
        if fecha and self._is_event_soon(fecha, days=30):
            signals.append("evento en menos de 30 días - URGENTE")
        
        # Múltiples canales de contacto
        contactos = sum([
            bool(prospecto.get("telefono")),
            bool(prospecto.get("email")),
            bool(prospecto.get("instagram"))
        ])
        if contactos >= 2:
            signals.append("múltiples canales de contacto disponibles")
        
        # Empresa + evento + contacto = oportunidad completa
        if prospecto.get("empresa") and prospecto.get("evento") and contactos >= 1:
            signals.append("oportunidad completa: empresa, evento y contacto")
        
        return signals
    
    async def _generate_recommendation(
        self, 
        prospecto: Dict, 
        score: int, 
        pos_signals: List[str],
        oportunidad: List[str]
    ) -> str:
        """Generar recomendación en texto natural usando LLM."""
        
        prompt = f"""
        Genera una recomendación comercial concisa (1-2 oraciones) para el equipo de ventas.
        
        Prospecto: {prospecto.get('empresa', 'Desconocido')}
        Evento: {prospecto.get('evento', 'No especificado')}
        Score: {score}/100
        Prioridad: {self._classify_priority(score)[0]}
        
        Señales positivas:
        {chr(10).join(f"- {s}" for s in pos_signals[:5])}
        
        Señales de oportunidad:
        {chr(10).join(f"- {s}" for s in oportunidad[:3])}
        
        La recomendación debe:
        - Ser concreta y accionable
        - Indicar cómo acercarse al prospecto
        - Mencionar qué destacar primero
        - Máximo 2 oraciones
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt=self.SYSTEM_PROMPT)
            return response.strip().replace('"', '')
        except Exception as e:
            logger.warning(f"[ANALISTA] Falló generación de recomendación: {e}")
            return f"Prospecto con score {score}. Contactar según prioridad."
    
    def _identify_missing_fields(self, prospecto: Dict) -> List[str]:
        """Identificar campos faltantes críticos."""
        critical_fields = ["telefono", "email", "fecha", "empresa"]
        return [f for f in critical_fields if not prospecto.get(f)]
    
    def _is_event_soon(self, fecha: str, days: int = 60) -> bool:
        """Verificar si un evento está próximo."""
        try:
            event_date = datetime.strptime(fecha, "%Y-%m-%d")
            return datetime.now() <= event_date <= datetime.now() + timedelta(days=days)
        except (ValueError, TypeError):
            return False


# Instancia singleton
analyst_agent = AnalystAgent()
```

---

## 9. AGENTE MEMORIA (AUKA-MEMORIA)

### 9.1 Especificación

| Atributo | Valor |
|----------|-------|
| Nombre | AUKA-MEMORIA |
| Tipo | Gestor de estado / Optimizador de contexto |
| Modelo | Sin LLM (lógica determinística pura) |
| Rol | Evitar duplicados, mantener historial, aprender |

### 9.2 Responsabilidades

- Registrar cada búsqueda realizada
- Detectar y bloquear duplicados antes de guardar
- Calcular rendimiento por fuente
- Mantener lista de empresas ya procesadas
- Proveer queries que mejor funcionaron al Explorador
- Generar reportes de eficiencia

### 9.3 Estructura de Datos en Supabase

```sql
-- Tabla: memoria_busquedas
CREATE TABLE memoria_busquedas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    fuente TEXT NOT NULL, -- google_maps | instagram | web
    fecha TIMESTAMP DEFAULT NOW(),
    resultados_totales INT DEFAULT 0,
    prospectos_nuevos INT DEFAULT 0,
    duracion_segundos INT DEFAULT 0,
    eficiencia FLOAT DEFAULT 0, -- nuevos / totales
    ciudad TEXT
);

-- Tabla: memoria_empresas
CREATE TABLE memoria_empresas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa TEXT,
    telefono TEXT,
    instagram TEXT,
    web TEXT,
    hash_identificador TEXT UNIQUE, -- MD5 para dedup rápido
    primera_vez_visto TIMESTAMP DEFAULT NOW(),
    ultima_vez_visto TIMESTAMP DEFAULT NOW(),
    veces_encontrado INT DEFAULT 1,
    procesado BOOLEAN DEFAULT false
);

-- Tabla: memoria_fuentes
CREATE TABLE memoria_fuentes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fuente TEXT UNIQUE,
    total_busquedas INT DEFAULT 0,
    total_prospectos INT DEFAULT 0,
    eficiencia_promedio FLOAT DEFAULT 0,
    ultima_busqueda TIMESTAMP,
    activa BOOLEAN DEFAULT true
);
```

### 9.4 Sistema de Deduplicación

**Estrategia 1: Hash MD5 (rápido, O(1))**
- Usar teléfono como identificador principal
- Fallback: instagram → web → nombre normalizado

**Estrategia 2: Fuzzy Matching (SequenceMatcher)**
- Umbral de similitud: 85%
- Para empresas encontradas por nombre sin identificador único

**Estrategia 3: Verificación en DB**
- Índice único en `hash_identificador`
- Update de contador si ya existe

### 9.5 Código del Agente Memoria

```python
# scripts/agents/memory.py
"""
AUKA-MEMORIA: Gestiona estado, historial y aprendizaje del sistema.
NO usa LLM - lógica determinística pura para máxima velocidad.
Principio: Persistencia total en Supabase (sobrevive reinicios).
"""

import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from scripts.database.supabase_client import SupabaseClient

logger = logging.getLogger("auka.memoria")


class MemoryAgent:
    """
    Agente Memoria: Deduplicación, aprendizaje y contexto histórico.
    100% determinista - sin LLM.
    """
    
    def __init__(self):
        self.db = SupabaseClient()
        self._local_cache: Dict[str, Dict] = {}  # Cache de últimas 100 empresas
        self._cache_max_size = 100
    
    # ═══════════════════════════════════════════════════════════════
    # TAREA: CHECK_DUPLICATE
    # ═══════════════════════════════════════════════════════════════
    
    async def check_duplicate(self, empresa_data: Dict) -> Dict[str, Any]:
        """
        Verificar si una empresa ya existe en el sistema.
        Estrategia: Hash MD5 → DB lookup → Fuzzy fallback.
        
        Returns:
            {"es_duplicado": bool, "registro_id": str|None, "veces_encontrado": int}
        """
        # Generar hash identificador
        hash_id = self._generate_hash(empresa_data)
        empresa_data["_hash"] = hash_id
        
        # 1. Verificar caché local (más rápido)
        if hash_id in self._local_cache:
            cached = self._local_cache[hash_id]
            logger.info(f"[MEMORIA] Duplicado encontrado en caché: {cached.get('empresa')}")
            return {
                "es_duplicado": True,
                "registro_id": cached.get("id"),
                "primera_vez_visto": cached.get("primera_vez_visto"),
                "veces_encontrado": cached.get("veces_encontrado", 1) + 1
            }
        
        # 2. Verificar en DB por hash
        try:
            result = self.db.table("memoria_empresas") \
                .select("*") \
                .eq("hash_identificador", hash_id) \
                .execute()
            
            if result.data:
                registro = result.data[0]
                # Actualizar contador y timestamp
                self._update_empresa_counter(registro["id"])
                
                # Actualizar caché
                self._add_to_cache(hash_id, registro)
                
                return {
                    "es_duplicado": True,
                    "registro_id": registro["id"],
                    "primera_vez_visto": registro.get("primera_vez_visto"),
                    "veces_encontrado": registro.get("veces_encontrado", 1) + 1
                }
        except Exception as e:
            logger.error(f"[MEMORIA] Error en DB lookup: {e}")
        
        # 3. Fuzzy matching por nombre (fallback)
        nombre_nuevo = empresa_data.get("empresa", "")
        if nombre_nuevo:
            es_dup, nombre_match = await self._fuzzy_check(nombre_nuevo)
            if es_dup:
                return {
                    "es_duplicado": True,
                    "registro_id": None,
                    "primera_vez_visto": None,
                    "veces_encontrado": 1,
                    "match_por": "fuzzy",
                    "nombre_similar": nombre_match
                }
        
        # No es duplicado - registrar nueva
        await self._register_new_empresa(empresa_data, hash_id)
        
        return {"es_duplicado": False}
    
    def _generate_hash(self, empresa: Dict) -> str:
        """Generar hash único basado en datos estables."""
        # Prioridad: teléfono > instagram > web > nombre
        identificador = (
            empresa.get("telefono") or 
            empresa.get("instagram") or 
            empresa.get("web") or 
            empresa.get("empresa", "").lower().strip()
        )
        return hashlib.md5(identificador.encode()).hexdigest()
    
    async def _fuzzy_check(self, nombre_nuevo: str, threshold: float = 0.85) -> tuple:
        """Verificar similitud fuzzy con empresas existentes."""
        try:
            result = self.db.table("memoria_empresas") \
                .select("empresa") \
                .execute()
            
            for reg in result.data:
                nombre_existente = reg.get("empresa", "")
                if nombre_existente:
                    similitud = SequenceMatcher(
                        None, 
                        nombre_nuevo.lower().strip(), 
                        nombre_existente.lower().strip()
                    ).ratio()
                    if similitud > threshold:
                        return True, nombre_existente
        except Exception as e:
            logger.error(f"[MEMORIA] Error en fuzzy check: {e}")
        
        return False, None
    
    async def _register_new_empresa(self, empresa: Dict, hash_id: str):
        """Registrar nueva empresa en memoria."""
        try:
            data = {
                "empresa": empresa.get("empresa"),
                "telefono": empresa.get("telefono"),
                "instagram": empresa.get("instagram"),
                "web": empresa.get("web"),
                "hash_identificador": hash_id
            }
            
            result = self.db.table("memoria_empresas").insert(data).execute()
            
            if result.data:
                self._add_to_cache(hash_id, result.data[0])
                logger.info(f"[MEMORIA] Nueva empresa registrada: {empresa.get('empresa')}")
                
        except Exception as e:
            logger.error(f"[MEMORIA] Error registrando empresa: {e}")
    
    def _update_empresa_counter(self, registro_id: str):
        """Actualizar contador de veces encontrado."""
        try:
            self.db.table("memoria_empresas") \
                .update({
                    "ultima_vez_visto": "NOW()",
                    "veces_encontrado": self.db.raw("veces_encontrado + 1")
                }) \
                .eq("id", registro_id) \
                .execute()
        except Exception as e:
            logger.error(f"[MEMORIA] Error actualizando contador: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # TAREA: LOG_SEARCH
    # ═══════════════════════════════════════════════════════════════
    
    async def log_search(
        self, 
        query: str, 
        fuente: str, 
        resultados_totales: int,
        prospectos_nuevos: int,
        duracion: int,
        ciudad: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registrar una búsqueda y calcular su eficiencia.
        
        Returns:
            {"registrado": bool, "eficiencia": float}
        """
        eficiencia = prospectos_nuevos / resultados_totales if resultados_totales > 0 else 0
        
        try:
            # Insertar registro de búsqueda
            self.db.table("memoria_busquedas").insert({
                "query": query,
                "fuente": fuente,
                "resultados_totales": resultados_totales,
                "prospectos_nuevos": prospectos_nuevos,
                "duracion_segundos": duracion,
                "eficiencia": eficiencia,
                "ciudad": ciudad
            }).execute()
            
            # Actualizar stats de la fuente
            await self._update_source_stats(fuente, eficiencia)
            
            logger.info(f"[MEMORIA] Búsqueda registrada: {query} | "
                       f"Eficiencia: {eficiencia:.2%}")
            
            return {"registrado": True, "eficiencia": eficiencia}
            
        except Exception as e:
            logger.error(f"[MEMORIA] Error registrando búsqueda: {e}")
            return {"registrado": False, "eficiencia": 0}
    
    async def _update_source_stats(self, fuente: str, eficiencia_nueva: float):
        """Actualizar estadísticas acumuladas de una fuente."""
        try:
            result = self.db.table("memoria_fuentes") \
                .select("*") \
                .eq("fuente", fuente) \
                .execute()
            
            if result.data:
                stats = result.data[0]
                n = stats["total_busquedas"]
                nuevo_promedio = (stats["eficiencia_promedio"] * n + eficiencia_nueva) / (n + 1)
                
                self.db.table("memoria_fuentes") \
                    .update({
                        "total_busquedas": n + 1,
                        "total_prospectos": stats["total_prospectos"] + 1,
                        "eficiencia_promedio": nuevo_promedio,
                        "ultima_busqueda": "NOW()"
                    }) \
                    .eq("fuente", fuente) \
                    .execute()
            else:
                self.db.table("memoria_fuentes").insert({
                    "fuente": fuente,
                    "total_busquedas": 1,
                    "total_prospectos": 1,
                    "eficiencia_promedio": eficiencia_nueva,
                    "ultima_busqueda": "NOW()"
                }).execute()
                
        except Exception as e:
            logger.error(f"[MEMORIA] Error actualizando stats: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # TAREA: GET_CONTEXT
    # ═══════════════════════════════════════════════════════════════
    
    async def get_context(self, scope: str = "last_24h") -> Dict[str, Any]:
        """
        Obtener contexto histórico para el Director.
        
        Returns:
            dict con queries, empresas, fuentes, ciudades, recomendación
        """
        try:
            # Calcular fecha límite según scope
            since = self._calculate_since(scope)
            
            # Queries recientes
            queries_result = self.db.table("memoria_busquedas") \
                .select("query, fuente, ciudad") \
                .gte("fecha", since) \
                .execute()
            
            queries_realizadas = list(set(q["query"] for q in queries_result.data if q.get("query")))
            ciudades_cubiertas = list(set(q["ciudad"] for q in queries_result.data if q.get("ciudad")))
            
            # Empresas procesadas
            empresas_result = self.db.table("memoria_empresas") \
                .select("empresa") \
                .eq("procesado", True) \
                .execute()
            
            empresas_procesadas = [e["empresa"] for e in empresas_result.data if e.get("empresa")]
            
            # Rendimiento por fuente
            fuentes_result = self.db.table("memoria_fuentes") \
                .select("fuente, eficiencia_promedio") \
                .execute()
            
            fuentes_rendimiento = {
                f["fuente"]: f.get("eficiencia_promedio", 0) 
                for f in fuentes_result.data
            }
            
            # Generar recomendación automática
            recomendacion = self._generate_recommendation(ciudades_cubiertas, fuentes_rendimiento)
            
            return {
                "queries_realizadas": queries_realizadas,
                "empresas_procesadas": empresas_procesadas,
                "fuentes_rendimiento": fuentes_rendimiento,
                "ciudades_cubiertas": ciudades_cubiertas,
                "recomendacion": recomendacion,
                "scope": scope,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[MEMORIA] Error obteniendo contexto: {e}")
            return self._default_context()
    
    # ═══════════════════════════════════════════════════════════════
    # TAREA: GET_BEST_QUERIES
    # ═══════════════════════════════════════════════════════════════
    
    async def get_best_queries(self, ciudad: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Obtener queries históricas con mejor eficiencia.
        
        Returns:
            Lista de dicts con query, fuente, eficiencia
        """
        try:
            query = self.db.table("memoria_busquedas") \
                .select("query, fuente, eficiencia") \
                .order("eficiencia", desc=True) \
                .limit(limit)
            
            if ciudad:
                query = query.eq("ciudad", ciudad)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"[MEMORIA] Error obteniendo mejores queries: {e}")
            return []
    
    # ═══════════════════════════════════════════════════════════════
    # TAREA: MARK_PROCESSED
    # ═══════════════════════════════════════════════════════════════
    
    async def mark_processed(self, empresa_id: str):
        """Marcar empresa como procesada."""
        try:
            self.db.table("memoria_empresas") \
                .update({"procesado": True}) \
                .eq("id", empresa_id) \
                .execute()
        except Exception as e:
            logger.error(f"[MEMORIA] Error marcando como procesada: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def _calculate_since(self, scope: str) -> str:
        """Calcular fecha límite para scope."""
        now = datetime.utcnow()
        scopes = {
            "last_24h": now - timedelta(hours=24),
            "last_week": now - timedelta(days=7),
            "last_month": now - timedelta(days=30),
            "all": now - timedelta(days=3650)  # 10 años = prácticamente todo
        }
        return scopes.get(scope, scopes["last_24h"]).isoformat()
    
    def _generate_recommendation(
        self, 
        ciudades_cubiertas: List[str], 
        fuentes_rendimiento: Dict
    ) -> str:
        """Generar recomendación automática basada en datos."""
        ciudades_todas = ["Caracas", "Valencia", "Maracay", "La Guaira"]
        ciudades_faltantes = [c for c in ciudades_todas if c not in ciudades_cubiertas]
        
        if ciudades_faltantes:
            return f"explorar {ciudades_faltantes[0]}, sin búsquedas recientes"
        
        # Recomendar fuente más eficiente
        if fuentes_rendimiento:
            mejor_fuente = max(fuentes_rendimiento, key=fuentes_rendimiento.get)
            return f"priorizar {mejor_fuente} (mayor eficiencia histórica)"
        
        return "rotar queries en ciudades existentes"
    
    def _default_context(self) -> Dict:
        """Contexto por defecto en caso de error."""
        return {
            "queries_realizadas": [],
            "empresas_procesadas": [],
            "fuentes_rendimiento": {},
            "ciudades_cubiertas": [],
            "recomendacion": "iniciar exploración desde cero",
            "scope": "error",
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _add_to_cache(self, hash_id: str, data: Dict):
        """Agregar a caché local con límite de tamaño."""
        self._local_cache[hash_id] = data
        
        # Mantener límite de caché
        if len(self._local_cache) > self._cache_max_size:
            # Eliminar el más antiguo (primero en insertarse)
            oldest = next(iter(self._local_cache))
            del self._local_cache[oldest]
    
    async def generar_reporte_eficiencia(self) -> Dict:
        """Generar reporte de eficiencia del sistema."""
        try:
            fuentes = self.db.table("memoria_fuentes").select("*").execute().data or []
            busquedas = self.db.table("memoria_busquedas").select("count", count="exact").execute()
            empresas = self.db.table("memoria_empresas").select("count", count="exact").execute()
            
            return {
                "total_busquedas": busquedas.count if hasattr(busquedas, 'count') else 0,
                "total_empresas_unicas": empresas.count if hasattr(empresas, 'count') else 0,
                "fuentes": [
                    {
                        "nombre": f["fuente"],
                        "eficiencia": f"{f.get('eficiencia_promedio', 0)*100:.0f}%",
                        "busquedas": f.get("total_busquedas", 0)
                    }
                    for f in fuentes
                ],
                "generado_en": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"[MEMORIA] Error generando reporte: {e}")
            return {"error": str(e)}


# Instancia singleton
memory_agent = MemoryAgent()
```

---

## 10. AGENTE CONVERSACIONAL (AUKA-CONVERSACIONAL)

### 10.1 Especificación

| Atributo | Valor |
|----------|-------|
| Nombre | AUKA-CONVERSACIONAL |
| Tipo | Interfaz de usuario / Orquestador de lenguaje natural |
| Canales | Telegram Bot + Dashboard (chat embebido) |
| Modelo | Kimi K2.5 |
| Rol | Ser la cara visible del sistema |

### 10.2 Clasificador de Intenciones

| Intención | Ejemplos | Acción |
|-----------|----------|--------|
| CONSULTA_DB | "dame prospectos", "cuántos leads tenemos" | Query a Supabase |
| ACTIVAR_BUSQUEDA | "busca eventos en Caracas", "encuentra empresas" | Delegar al Director |
| CAMBIAR_ESTADO | "marca como contactada", "actualiza estado" | Update en Supabase |
| RESUMEN | "dame un resumen", "qué encontró el sistema" | Generar reporte |
| AYUDA | "qué puedes hacer", "cómo funciona" | Mostrar capacidades |
| OTRO | cualquier otro mensaje | Respuesta genérica o pedir aclaración |

### 10.3 Código del Agente Conversacional

```python
# scripts/agents/conversational.py
"""
AUKA-CONVERSACIONAL: Interfaz humana del sistema.
Canales: Telegram + Dashboard
Principio: Interpreta, consulta y delega. Nunca ejecuta directamente.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from scripts.utils.llm_client import LLMClient
from scripts.utils.validators import validate_json_output
from scripts.database.supabase_client import SupabaseClient

logger = logging.getLogger("auka.conversacional")


class ConversationalAgent:
    """
    Agente Conversacional: Punto de entrada humano al sistema.
    Clasifica intenciones y enruta al agente correcto.
    """
    
    SYSTEM_PROMPT = """
    Eres AUKA-CONVERSACIONAL, el agente de interfaz del sistema autónomo de 
    prospección de Aguas Arauka.
    
    REGLAS OBLIGATORIAS:
    1. Responde SIEMPRE en español
    2. Sé claro, directo y útil
    3. NO inventes datos de prospectos
    4. Si no tienes datos, dilo claramente
    5. Antes de ejecutar acciones importantes, confirma
    6. Mantén un tono profesional pero conversacional
    7. SIEMPRE devuelve JSON con "respuesta_texto" y "accion_ejecutada"
    
    CANALES:
    - Telegram: texto plano, emojis, máximo 3-4 párrafos
    - Dashboard: datos enriquecidos, tablas, métricas
    
    CAPACIDADES:
    - Consultar prospectos en base de datos
    - Filtrar por ciudad, prioridad, tipo de evento
    - Activar búsquedas nuevas (vía Director)
    - Actualizar estado de prospectos
    - Mostrar estadísticas del sistema
    """
    
    MENSAJE_AYUDA = """
    ¡Hola! Soy AUKA, tu asistente de prospección para Aguas Arauka. Esto es lo que puedo hacer:

    🔍 BUSCAR
    • "busca eventos en Caracas"
    • "encuentra empresas en Valencia"
    • "rastrea Instagram de eventos deportivos"

    📊 CONSULTAR
    • "dame los prospectos de hoy"
    • "muéstrame los de alta prioridad"
    • "cuántos leads tenemos en Maracay"

    📈 ESTADÍSTICAS
    • "resumen de hoy"
    • "cuántas búsquedas hice esta semana"

    ✏️ ACTUALIZAR
    • "marca XYZ como contactada"
    • "agrega nota a Eventos Beta"

    Puedes escribirme en lenguaje natural. ¡Estoy listo para trabajar!
    """
    
    def __init__(self):
        self.llm = LLMClient(primary_model="kimi-k2.5")
        self.db = SupabaseClient()
    
    async def process_message(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesar mensaje del usuario.
        
        Args:
            input_data: dict con canal, user_id, mensaje, contexto
            
        Returns:
            dict con respuesta_texto, accion_ejecutada, datos
        """
        canal = input_data.get("canal", "telegram")
        mensaje = input_data.get("mensaje", "")
        user_id = input_data.get("user_id", "")
        contexto = input_data.get("contexto", [])
        
        logger.info(f"[CONVERSACIONAL] Mensaje de {canal}: {mensaje[:50]}")
        
        # ── 1. CLASIFICAR INTENCIÓN ─────────────────────────────────
        intencion = await self._clasificar_intencion(mensaje)
        
        # ── 2. EJECUTAR ACCIÓN ──────────────────────────────────────
        if intencion == "CONSULTA_DB":
            result = await self._handle_consulta(mensaje, canal)
        elif intencion == "ACTIVAR_BUSQUEDA":
            result = await self._handle_busqueda(mensaje, canal, user_id)
        elif intencion == "CAMBIAR_ESTADO":
            result = await self._handle_update(mensaje, canal)
        elif intencion == "RESUMEN":
            result = await self._handle_resumen(canal)
        elif intencion == "AYUDA":
            result = self._handle_ayuda(canal)
        else:
            result = await self._handle_generico(mensaje, contexto, canal)
        
        # ── 3. FORMATEAR RESPUESTA ──────────────────────────────────
        formatted = self._format_response(result, canal)
        
        # Guardar contexto
        self._guardar_contexto(user_id, mensaje, formatted["respuesta_texto"])
        
        return formatted
    
    async def _clasificar_intencion(self, mensaje: str) -> str:
        """Clasificar intención del mensaje usando LLM."""
        
        prompt = f"""
        Clasifica este mensaje en UNA de estas categorías:
        - CONSULTA_DB: usuario pide ver datos de prospectos
        - ACTIVAR_BUSQUEDA: usuario quiere buscar algo nuevo
        - CAMBIAR_ESTADO: usuario quiere actualizar un registro
        - RESUMEN: usuario pide estadísticas o resumen
        - AYUDA: usuario pregunta qué puedo hacer
        - OTRO: cualquier otra cosa
        
        Mensaje: "{mensaje}"
        
        Responde SOLO con la categoría, sin texto adicional.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt=self.SYSTEM_PROMPT)
            intencion = response.strip().upper().split()[0]
            
            validas = ["CONSULTA_DB", "ACTIVAR_BUSQUEDA", "CAMBIAR_ESTADO", 
                      "RESUMEN", "AYUDA", "OTRO"]
            return intencion if intencion in validas else "OTRO"
            
        except Exception as e:
            logger.error(f"[CONVERSACIONAL] Error clasificando: {e}")
            return "OTRO"
    
    async def _handle_consulta(self, mensaje: str, canal: str) -> Dict:
        """Manejar consulta a base de datos."""
        # Extraer filtros con LLM
        filtros = await self._extraer_filtros(mensaje)
        
        # Construir query
        query = self.db.table("prospectos").select("*")
        
        if filtros.get("ciudad"):
            query = query.eq("ciudad", filtros["ciudad"])
        if filtros.get("prioridad"):
            query = query.eq("prioridad", filtros["prioridad"])
        if filtros.get("tipo_evento"):
            query = query.eq("tipo_evento", filtros["tipo_evento"])
        
        resultados = query.limit(20).execute()
        
        return {
            "tipo": "consulta",
            "datos": resultados.data or [],
            "filtros": filtros,
            "total": len(resultados.data) if resultados.data else 0
        }
    
    async def _extraer_filtros(self, mensaje: str) -> Dict:
        """Extraer filtros de búsqueda del mensaje."""
        prompt = f"""
        Extrae los filtros de búsqueda de este mensaje.
        Devuelve JSON con: ciudad, prioridad, tipo_evento
        Si no se menciona un filtro, devuelve null.
        
        Mensaje: "{mensaje}"
        
        Ciudades válidas: Caracas, Valencia, Maracay, La Guaira
        Prioridades válidas: ALTA, MEDIA, BAJA
        Tipos de evento válidos: deportivo, corporativo, social, cultural, gastronomico, religioso
        """
        
        try:
            response = self.llm.generate(prompt)
            return validate_json_output(response)
        except Exception:
            return {}
    
    async def _handle_busqueda(self, mensaje: str, canal: str, user_id: str) -> Dict:
        """Manejar activación de búsqueda."""
        # Extraer parámetros
        prompt = f"""
        Extrae de este mensaje:
        - objetivo: qué buscar (eventos, empresas, etc.)
        - ciudad: dónde buscar
        
        Mensaje: "{mensaje}"
        
        Devuelve JSON: {{"objetivo": "...", "ciudad": "..."}}
        """
        
        try:
            response = self.llm.generate(prompt)
            params = validate_json_output(response)
        except Exception:
            params = {"objetivo": "eventos", "ciudad": "Caracas"}
        
        # Confirmar antes de ejecutar
        confirmacion = (
            f"Voy a iniciar una búsqueda de {params.get('objetivo', 'eventos')} "
            f"en {params.get('ciudad', 'Venezuela')}. "
            f"¿Confirmas? (sí/no)"
        )
        
        return {
            "tipo": "confirmacion_busqueda",
            "mensaje": confirmacion,
            "params": params,
            "pendiente_confirmacion": True
        }
    
    async def _handle_update(self, mensaje: str, canal: str) -> Dict:
        """Manejar actualización de estado."""
        return {
            "tipo": "update",
            "mensaje": "Función de actualización en desarrollo. Usa el dashboard para editar registros.",
            "accion_ejecutada": "none"
        }
    
    async def _handle_resumen(self, canal: str) -> Dict:
        """Generar resumen del sistema."""
        try:
            # Estadísticas básicas
            prospectos = self.db.table("prospectos").select("count", count="exact").execute()
            
            hoy = datetime.now().strftime("%Y-%m-%d")
            hoy_result = self.db.table("prospectos") \
                .select("count", count="exact") \
                .gte("creado_en", hoy) \
                .execute()
            
            return {
                "tipo": "resumen",
                "datos": {
                    "total_prospectos": getattr(prospectos, 'count', 0),
                    "nuevos_hoy": getattr(hoy_result, 'count', 0),
                    "fecha": hoy
                }
            }
        except Exception as e:
            return {
                "tipo": "resumen",
                "datos": {},
                "error": str(e)
            }
    
    def _handle_ayuda(self, canal: str) -> Dict:
        """Mostrar mensaje de ayuda."""
        return {
            "tipo": "ayuda",
            "mensaje": self.MENSAJE_AYUDA
        }
    
    async def _handle_generico(self, mensaje: str, contexto: List, canal: str) -> Dict:
        """Manejar mensaje genérico con LLM."""
        prompt = f"""
        Responde a este mensaje de forma útil y concisa.
        Si no entiendes lo que quiere, pide aclaración.
        
        Mensaje: "{mensaje}"
        Contexto reciente: {len(contexto)} interacciones
        
        Responde en 1-2 oraciones máximo.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt=self.SYSTEM_PROMPT)
            return {
                "tipo": "generico",
                "mensaje": response.strip()
            }
        except Exception as e:
            return {
                "tipo": "error",
                "mensaje": "Lo siento, no pude procesar tu mensaje. ¿Puedes reformularlo?"
            }
    
    def _format_response(self, result: Dict, canal: str) -> Dict[str, Any]:
        """Formatear respuesta según el canal."""
        
        if result["tipo"] == "consulta":
            if canal == "telegram":
                texto = self._format_telegram_prospectos(result["datos"], result.get("total", 0))
            else:
                texto = self._format_dashboard_prospectos(result["datos"])
                
        elif result["tipo"] == "confirmacion_busqueda":
            texto = result["mensaje"]
            
        elif result["tipo"] == "resumen":
            datos = result.get("datos", {})
            texto = (
                f"📊 Resumen de hoy ({datos.get('fecha', 'hoy')}):\n"
                f"• Total prospectos: {datos.get('total_prospectos', 0)}\n"
                f"• Nuevos hoy: {datos.get('nuevos_hoy', 0)}"
            )
            
        elif result["tipo"] == "ayuda":
            texto = result["mensaje"]
            
        elif result["tipo"] == "generico":
            texto = result["mensaje"]
            
        elif result["tipo"] == "update":
            texto = result["mensaje"]
            
        else:
            texto = "No entendí tu solicitud. Escribe 'ayuda' para ver opciones."
        
        return {
            "respuesta_texto": texto,
            "accion_ejecutada": result.get("tipo", "none"),
            "datos": result.get("datos"),
            "canal": canal,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _format_telegram_prospectos(self, prospectos: List[Dict], total: int) -> str:
        """Formatear lista de prospectos para Telegram."""
        if not prospectos:
            return "No encontré prospectos con esos filtros."
        
        texto = f"Encontré {total} prospectos:\n\n"
        
        for i, p in enumerate(prospectos[:5], 1):
            texto += f"{i}. *{p.get('empresa', 'Sin nombre')}*\n"
            if p.get("evento"):
                texto += f"   📅 {p['evento']}\n"
            if p.get("telefono"):
                texto += f"   📞 {p['telefono']}\n"
            texto += f"   📍 {p.get('ciudad', '?')} | Score: {p.get('score', '?')}\n\n"
        
        if total > 5:
            texto += f"...y {total - 5} más en el dashboard"
        
        return texto
    
    def _format_dashboard_prospectos(self, prospectos: List[Dict]) -> str:
        """Formatear para dashboard (JSON estructurado)."""
        return json.dumps(prospectos, ensure_ascii=False, indent=2)
    
    def _guardar_contexto(self, user_id: str, msg_user: str, msg_agent: str):
        """Guardar contexto conversacional."""
        # Implementar con Supabase o caché en memoria
        pass


# Instancia singleton
conversational_agent = ConversationalAgent()
```

---

## 11. INTEGRACIÓN DASHBOARD

### 11.1 Especificación del Dashboard

| Aspecto | Especificación |
|---------|---------------|
| Framework | Next.js (App Router) |
| Estilo | Tailwind CSS, Dark mode, Glassmorphism |
| Animaciones | GSAP (ScrollTrigger obligatorio) |
| Mapa | Mapbox GL o Leaflet |
| Data Fetching | React Query |
| Backend | Supabase (DB + Auth) |

### 11.2 Módulos Principales

| Módulo | Componentes | Animaciones GSAP |
|--------|------------|------------------|
| Overview | KPIs, Gráficas por ciudad/tipo | fade+slide staggered, count-up |
| Mapa | Markers geolocalizados, clusters | zoom suave, scale bounce, glow hover |
| Tabla Prospectos | Filtros, búsqueda, ordenamiento | fade+reflow, highlight hover |
| Detalle Empresa | Info completa, notas, acciones | slide-in lateral, tabs fluidas |
| Actividad Agente | Log tipo terminal | typing effect, auto-scroll |
| Chat Agente | Input, historial, respuestas | typing animation, burbuja |

### 11.3 Colores

```css
--bg-primary: #0B0F1A;
--primary: #3B82F6;      /* Azul eléctrico */
--accent: #10B981;       /* Verde (acciones) */
--text-primary: #F9FAFB;
--text-secondary: #9CA3AF;
--glass-bg: rgba(255, 255, 255, 0.05);
--glass-border: rgba(255, 255, 255, 0.1);
```

---

## 12. FLUJO COMPLETO DE DATOS

### 12.1 Flujo de Búsqueda Completa

```
[Usuario] 
  "Busca eventos deportivos en Caracas"
    ↓
[AUKA-CONVERSACIONAL]
  Clasifica: ACTIVAR_BUSQUEDA
  Delega al Director
    ↓
[AUKA-DIRECTOR]
  Fase 1: ENTENDER → eventos deportivos, Caracas
  Fase 2: CLASIFICAR → tipo: search, prioridad: high
  Fase 3: PLANIFICAR → pipeline completo
  Fase 4: DELEGAR → secuencia de actions
    ↓
[AUKA-MEMORIA]
  Consulta: ¿qué ya se hizo?
  Responde: contexto + mejores queries
    ↓
[AUKA-EXPLORADOR]
  Genera queries optimizadas:
  - "eventos deportivos caracas"
  - "productoras deportivas caracas"  
  - "#eventosdeportivoscaracas"
    ↓
[AUKA-SCRAPER]
  Ejecuta en paralelo:
  - Google Maps: 15 empresas
  - Instagram: 8 perfiles
    ↓
[AUKA-ESTRUCTURADOR]
  Procesa 23 registros crudos
  Genera 18 JSON limpios
  5 descartados (confianza baja)
    ↓
[AUKA-ANALISTA]
  Evalúa 18 prospectos:
  - 5 ALTA prioridad (score 80-100)
  - 8 MEDIA prioridad (score 50-79)
  - 5 BAJA prioridad (score <50)
    ↓
[AUKA-MEMORIA]
  Verifica duplicados: 3 encontrados
  Registra 15 nuevos prospectos
  Actualiza eficiencia de fuentes
    ↓
[SUPABASE]
  Guarda 15 prospectos en tabla prospectos
    ↓
[AUKA-CONVERSACIONAL]
  Formatea respuesta:
  "Encontré 15 nuevos prospectos en Caracas:
   5 de alta prioridad listos para contactar..."
    ↓
[Usuario] ✓
```

### 12.2 Flujo de Consulta

```
[Usuario]
  "Dame prospectos de alta prioridad en Valencia"
    ↓
[AUKA-CONVERSACIONAL]
  Clasifica: CONSULTA_DB
  Extrae filtros: prioridad=ALTA, ciudad=Valencia
    ↓
[SUPABASE]
  SELECT * FROM prospectos 
  WHERE prioridad = 'ALTA' AND ciudad = 'Valencia'
    ↓
[AUKA-CONVERSACIONAL]
  Formatea resultados
    ↓
[Usuario] ✓
```

---

## 13. CONFIGURACIÓN Y DESPLIEGUE

### 13.1 Variables de Entorno (.env)

```bash
# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC...

# Modelos LLM
KIMI_API_KEY=sk-...
KIMI_MODEL=kimi-k2.5
GEMMA_API_KEY=...
DEEPSEEK_API_KEY=...

# Configuración
LOG_LEVEL=INFO
SCRAPER_DELAY_MIN=1.5
SCRAPER_DELAY_MAX=4.0
MAX_RESULTS_PER_QUERY=20
```

### 13.2 Dependencias (requirements.txt)

```
# Core
python-telegram-bot>=20.0
supabase-py>=2.0
python-dotenv>=1.0

# Scraping
playwright>=1.40
requests>=2.31
beautifulsoup4>=4.12

# LLM
openai>=1.0  # Para conectores compatibles

# Utilidades
pydantic>=2.0
python-json-logger>=2.0

# Dashboard (Next.js separado)
# Ver package.json en /dashboard
```

### 13.3 Inicialización de Base de Datos

```bash
# Ejecutar scripts/database/schemas.sql en Supabase SQL Editor
# Ver archivo schemas.py para definiciones completas
```

### 13.4 Punto de Entrada (main.py)

```python
# main.py
"""
AUKA System - Punto de entrada principal
Inicializa todos los agentes y coordina el sistema.
"""

import asyncio
import logging
from scripts.agents.director import director_agent
from scripts.agents.conversational import conversational_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Inicializar sistema AUKA."""
    print("🚀 AUKA System v2.0 - Iniciando...")
    print("✅ Agentes cargados: Director, Explorador, Scraper, Estructurador, Analista, Memoria, Conversacional")
    
    # Aquí se inicia el bot de Telegram o el servidor API
    # await start_telegram_bot()
    # await start_api_server()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## APÉNDICE A: REGLAS ANTI-ALUCINACIÓN DEL SISTEMA

1. **Nunca inventar datos**: Si un campo no existe → `null`, nunca "desconocido"
2. **Nunca inventar empresas**: El Explorador solo propone dónde buscar
3. **Nunca afirmar búsquedas no ejecutadas**: Si está en proceso → "en proceso"
4. **Score basado en datos**: El Analista usa solo datos recibidos, no suposiciones
5. **Confirmación previa**: El Conversacional confirma antes de acciones importantes
6. **Citar fuentes**: Siempre indicar si los datos vienen de DB o búsqueda reciente
7. **JSON obligatorio**: Todos los agentes devuelven JSON válido, nunca texto libre

## APÉNDICE B: FALLBACKS Y RECUPERACIÓN

| Fallo | Fallback | Acción |
|-------|----------|--------|
| LLM principal falla | Usar modelo backup | Gemma 4B o DeepSeek |
| Scraper bloqueado | Cambiar fuente | Maps → Instagram → Web |
| Datos incompletos | Enrichment | Re-scrapear con query refinada |
| Duplicado detectado | Ignorar | Actualizar contador, no guardar |
| Timeout LLM (10s) | Devolver error limpio | Log y continuar con siguiente |
| Instagram bloqueado | Delay aumentado | 5-10s + rotación UA |
| Sin resultados | Refinar query | Explorador genera variantes |

## APÉNDICE C: MÉTRICAS DE ÉXITO

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Prospectos nuevos/día | 15+ | Memoria.log_search |
| Score promedio | >60 | Analista.score |
| Duplicados evitados | >80% | Memoria.check_duplicate |
| Tiempo búsqueda completa | <5 min | timestamps |
| Eficiencia Google Maps | >60% | prospectos_nuevos/totales |
| Eficiencia Instagram | >40% | prospectos_nuevos/totales |

---

**FIN DEL DOCUMENTO TÉCNICO**

*Sistema AUKA v2.0 - Listo para producción*
