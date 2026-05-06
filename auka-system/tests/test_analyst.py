"""
Tests para AUKA-ANALISTA
Valida scoring determinista y clasificación de prioridad.
"""

import pytest
import asyncio
from scripts.agents.analyst import AnalystAgent


@pytest.fixture
def analyst():
    return AnalystAgent()


@pytest.fixture
def prospecto_completo():
    return {
        "empresa": "XYZ Events",
        "evento": "Fitness Caracas 2026",
        "tipo_evento": "deportivo",
        "fecha": "2026-06-15",
        "ciudad": "Caracas",
        "telefono": "+58-412-1234567",
        "email": "info@xyzevents.com",
        "instagram": "@xyzevents",
        "web": "https://xyzevents.com"
    }


@pytest.fixture
def prospecto_incompleto():
    return {
        "empresa": None,
        "evento": "Gran Feria Valencia",
        "tipo_evento": "corporativo",
        "fecha": None,
        "ciudad": "Valencia",
        "telefono": None,
        "email": None,
        "instagram": "@feriavlc",
        "web": None
    }


class TestAnalystScoring:
    """Tests para el sistema de scoring."""
    
    def test_score_completo(self, analyst, prospecto_completo):
        score, pos, neg = analyst._calculate_score(prospecto_completo)
        assert score == 100
        assert len(pos) >= 6
        assert len(neg) == 0
    
    def test_score_incompleto(self, analyst, prospecto_incompleto):
        score, pos, neg = analyst._calculate_score(prospecto_incompleto)
        assert score <= 40
        assert len(neg) >= 2
    
    def test_score_maximo(self, analyst, prospecto_completo):
        score, _, _ = analyst._calculate_score(prospecto_completo)
        assert score <= 100
    
    def test_score_minimo(self, analyst):
        vacio = {"empresa": None, "telefono": None, "email": None, "fecha": None}
        score, _, _ = analyst._calculate_score(vacio)
        assert score == 0


class TestPriorityClassification:
    """Tests para clasificación de prioridad."""
    
    def test_prioridad_alta(self, analyst):
        assert analyst._classify_priority(85) == ("ALTA", "contactar esta semana")
        assert analyst._classify_priority(100) == ("ALTA", "contactar esta semana")
    
    def test_prioridad_media(self, analyst):
        assert analyst._classify_priority(60) == ("MEDIA", "contactar este mes")
        assert analyst._classify_priority(79) == ("MEDIA", "contactar este mes")
    
    def test_prioridad_baja(self, analyst):
        assert analyst._classify_priority(30) == ("BAJA", "enriquecer antes de contactar")
        assert analyst._classify_priority(0) == ("BAJA", "enriquecer antes de contactar")


class TestEventDateCheck:
    """Tests para verificación de fechas de eventos."""
    
    def test_evento_proximo(self, analyst):
        # Fecha dentro de 60 días
        from datetime import datetime, timedelta
        fecha_futura = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        assert analyst._is_event_soon(fecha_futura) == True
    
    def test_evento_lejano(self, analyst):
        from datetime import datetime, timedelta
        fecha_lejana = (datetime.now() + timedelta(days=100)).strftime("%Y-%m-%d")
        assert analyst._is_event_soon(fecha_lejana) == False
    
    def test_fecha_invalida(self, analyst):
        assert analyst._is_event_soon("fecha-invalida") == False
        assert analyst._is_event_soon(None) == False


class TestOpportunitySignals:
    """Tests para detección de señales de oportunidad."""
    
    def test_multiple_canales(self, analyst):
        prospecto = {"telefono": "+58", "email": "test@test.com", "instagram": "@test"}
        signals = analyst._detect_opportunity_signals(prospecto)
        assert any("múltiples canales" in s for s in signals)
    
    def test_oportunidad_completa(self, analyst):
        from datetime import datetime, timedelta
        fecha = (datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d")
        prospecto = {
            "empresa": "Test", "evento": "Evento", "telefono": "+58",
            "fecha": fecha
        }
        signals = analyst._detect_opportunity_signals(prospecto)
        assert any("URGENTE" in s for s in signals)


@pytest.mark.asyncio
class TestAnalystIntegration:
    """Tests de integración async."""
    
    async def test_evaluate_completo(self, analyst, prospecto_completo):
        result = await analyst.evaluate(prospecto_completo)
        assert result["score"] >= 80
        assert result["prioridad"] == "ALTA"
        assert result["accion_recomendada"] == "contactar esta semana"
        assert len(result["señales_positivas"]) > 0
        assert result["enriquecer"] == False
    
    async def test_evaluate_incompleto(self, analyst, prospecto_incompleto):
        result = await analyst.evaluate(prospecto_incompleto)
        assert result["score"] < 50
        assert result["prioridad"] == "BAJA"
        assert result["enriquecer"] == True
    
    async def test_evaluate_batch(self, analyst, prospecto_completo, prospecto_incompleto):
        results = await analyst.evaluate_batch([prospecto_completo, prospecto_incompleto])
        assert len(results) == 2
        assert results[0]["analisis"]["score"] > results[1]["analisis"]["score"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
