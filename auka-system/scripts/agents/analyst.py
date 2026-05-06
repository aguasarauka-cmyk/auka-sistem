"""
AUKA-ANALISTA: Evalúa la calidad comercial de prospectos.
Modelo: Kimi K2.5 (solo para recomendación en texto natural)
Scoring: 100% determinista (sin LLM, más rápido)
"""

import logging
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

from scripts.utils.llm_client import LLMClient

logger = logging.getLogger("auka.analista")


class AnalystAgent:
    """
    Agente Analista: Evalúa prospectos y asigna score de prioridad.
    Scoring determinista + recomendación con LLM.
    """
    
    SYSTEM_PROMPT = """
    Eres AUKA-ANALISTA. Evalúa prospectos para Aguas Arauka.
    Producto: agua embotellada premium. Cliente ideal: eventos 50+ personas.
    Sé crítico: sin contacto = baja prioridad.
    """
    
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
    
    CITIES_TOP = ["caracas", "valencia", "maracay", "la guaira"]
    EVENT_TYPES_TOP = ["corporativo", "deportivo"]
    
    def __init__(self):
        self.llm = LLMClient(primary_model="kimi-k2.5")
    
    async def evaluate(self, prospecto: Dict) -> Dict:
        """
        Evaluar un prospecto y generar análisis completo.
        
        Pipeline: CALCULAR SCORE → CLASIFICAR → DETECTAR SEÑALES → RECOMENDAR
        """
        logger.info(f"[ANALISTA] Evaluando: {prospecto.get('empresa', 'N/A')}")
        
        # 1. SCORE determinista
        score, pos_signals, neg_signals = self._calculate_score(prospecto)
        
        # 2. CLASIFICAR
        prioridad, accion = self._classify_priority(score)
        
        # 3. SEÑALES DE OPORTUNIDAD
        oportunidad = self._detect_opportunity_signals(prospecto)
        
        # 4. RECOMENDACIÓN con LLM
        recomendacion = await self._generate_recommendation(prospecto, score, pos_signals)
        
        # 5. CAMPOS FALTANTES
        campos_faltantes = [f for f in ["telefono", "email", "fecha", "empresa"] if not prospecto.get(f)]
        
        return {
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
    
    async def evaluate_batch(self, prospectos: List[Dict]) -> List[Dict]:
        """Evaluar múltiples prospectos."""
        return [await self.evaluate(p) for p in prospectos]
    
    def _calculate_score(self, prospecto: Dict) -> Tuple[int, List[str], List[str]]:
        """Calcular score determinista."""
        score = 0
        pos = []
        neg = []
        
        if prospecto.get("telefono"):
            score += 20; pos.append("tiene teléfono directo")
        else:
            neg.append("sin teléfono")
        
        fecha = prospecto.get("fecha")
        if fecha and self._is_event_soon(fecha):
            score += 20; pos.append("tiene evento próximo")
        elif fecha:
            pos.append("tiene fecha pero evento lejano")
        else:
            neg.append("sin fecha")
        
        if prospecto.get("email"):
            score += 15; pos.append("tiene email")
        else:
            neg.append("sin email")
        
        if prospecto.get("instagram"):
            score += 15; pos.append("activa en Instagram")
        
        if prospecto.get("web"):
            score += 10; pos.append("tiene web")
        
        if prospecto.get("empresa"):
            score += 10; pos.append("empresa identificada")
        else:
            neg.append("sin empresa")
        
        ciudad = (prospecto.get("ciudad") or "").lower()
        if any(c in ciudad for c in self.CITIES_TOP):
            score += 5; pos.append("ciudad prioritaria")
        
        tipo = (prospecto.get("tipo_evento") or "").lower()
        if tipo in self.EVENT_TYPES_TOP:
            score += 5; pos.append("tipo prioritario")
        
        return min(score, 100), pos, neg
    
    def _classify_priority(self, score: int) -> Tuple[str, str]:
        """Clasificar prioridad."""
        if score >= 80: return "ALTA", "contactar esta semana"
        elif score >= 50: return "MEDIA", "contactar este mes"
        return "BAJA", "enriquecer antes de contactar"
    
    def _detect_opportunity_signals(self, prospecto: Dict) -> List[str]:
        """Detectar señales de oportunidad adicionales."""
        signals = []
        
        fecha = prospecto.get("fecha")
        if fecha and self._is_event_soon(fecha, days=30):
            signals.append("evento en <30 días - URGENTE")
        
        contactos = sum([
            bool(prospecto.get("telefono")),
            bool(prospecto.get("email")),
            bool(prospecto.get("instagram"))
        ])
        if contactos >= 2:
            signals.append("múltiples canales de contacto")
        
        if prospecto.get("empresa") and prospecto.get("evento") and contactos >= 1:
            signals.append("oportunidad completa")
        
        return signals
    
    async def _generate_recommendation(self, prospecto: Dict, score: int, pos_signals: List[str]) -> str:
        """Generar recomendación con LLM."""
        prompt = f"""
        Genera recomendación comercial concisa (1-2 oraciones).
        
        Prospecto: {prospecto.get('empresa', 'Desconocido')}
        Evento: {prospecto.get('evento', 'No especificado')}
        Score: {score}/100
        Señales: {', '.join(pos_signals[:5])}
        
        Indica cómo acercarse y qué mencionar primero.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt=self.SYSTEM_PROMPT)
            return response.strip().replace('"', '')
        except Exception:
            return f"Prospecto con score {score}. Contactar según prioridad."
    
    def _is_event_soon(self, fecha: str, days: int = 60) -> bool:
        """Verificar si evento está próximo."""
        try:
            event_date = datetime.strptime(fecha, "%Y-%m-%d")
            return datetime.now() <= event_date <= datetime.now() + timedelta(days=days)
        except (ValueError, TypeError):
            return False


# Instancia singleton
analyst_agent = AnalystAgent()
