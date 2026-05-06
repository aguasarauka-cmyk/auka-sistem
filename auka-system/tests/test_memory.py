"""
Tests para AUKA-MEMORIA
Valida deduplicación, hashing y contexto histórico.
"""

import pytest
import asyncio
from scripts.agents.memory import MemoryAgent


@pytest.fixture
def memory():
    return MemoryAgent()


@pytest.fixture
def empresa_test():
    return {
        "empresa": "Eventos XYZ",
        "telefono": "+58-412-1234567",
        "instagram": "@eventosxyz",
        "web": "https://eventosxyz.com"
    }


class TestHashGeneration:
    """Tests para generación de hashes."""
    
    def test_hash_telefono(self, memory, empresa_test):
        hash1 = memory._generate_hash(empresa_test)
        assert len(hash1) == 32  # MD5 = 32 hex chars
        
        # Misma empresa, mismo hash
        hash2 = memory._generate_hash(empresa_test)
        assert hash1 == hash2
    
    def test_hash_diferente_telefono(self, memory):
        emp1 = {"telefono": "+58-412-1111111"}
        emp2 = {"telefono": "+58-412-2222222"}
        assert memory._generate_hash(emp1) != memory._generate_hash(emp2)
    
    def test_hash_fallback(self, memory):
        # Sin teléfono, usa instagram
        emp = {"instagram": "@test", "empresa": "Test"}
        h = memory._generate_hash(emp)
        assert len(h) == 32
    
    def test_hash_nombre_fallback(self, memory):
        # Solo nombre
        emp = {"empresa": "Test Corp"}
        h = memory._generate_hash(emp)
        assert len(h) == 32


class TestConfidenceCalculation:
    """Tests para cálculo de confianza."""
    
    def test_confianza_alta(self, memory):
        data = {"empresa": "X", "evento": "Y", "telefono": "Z", "email": "A", "instagram": "B"}
        assert memory._calculate_confidence(data) == "alta"
    
    def test_confianza_media(self, memory):
        data = {"empresa": "X", "ciudad": "Caracas"}
        assert memory._calculate_confidence(data) == "media"
    
    def test_confianza_baja(self, memory):
        data = {}
        assert memory._calculate_confidence(data) == "baja"


class TestCache:
    """Tests para caché local."""
    
    def test_cache_add(self, memory):
        memory._add_to_cache("hash1", {"id": "1", "empresa": "Test"})
        assert "hash1" in memory._local_cache
    
    def test_cache_limit(self, memory):
        # Llenar caché más allá del límite
        for i in range(110):
            memory._add_to_cache(f"hash{i}", {"id": str(i)})
        assert len(memory._local_cache) <= memory._cache_max_size


class TestRecommendations:
    """Tests para generación de recomendaciones."""
    
    def test_recomendacion_ciudad_faltante(self, memory):
        rec = memory._generate_recommendation(["Caracas"], {})
        assert "explorar" in rec.lower()
    
    def test_recomendacion_fuente(self, memory):
        rec = memory._generate_recommendation(
            ["Caracas", "Valencia", "Maracay", "La Guaira"],
            {"google_maps": 0.8, "instagram": 0.4}
        )
        assert "priorizar" in rec.lower()
    
    def test_recomendacion_default(self, memory):
        rec = memory._generate_recommendation([], {})
        assert "rotar" in rec.lower()


class TestScopeCalculation:
    """Tests para cálculo de fechas de scope."""
    
    def test_scope_24h(self, memory):
        since = memory._calculate_since("last_24h")
        assert isinstance(since, str)
    
    def test_scope_invalid(self, memory):
        since = memory._calculate_since("invalid")
        assert isinstance(since, str)  # Debe retornar default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
