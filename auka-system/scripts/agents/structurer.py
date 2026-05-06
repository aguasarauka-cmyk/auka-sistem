"""
AUKA-ESTRUCTURADOR: Convierte datos crudos en JSON estructurado.
Modelo: Gemma 4B (principal), Kimi K2.5 (textos complejos)
Principio: Solo transforma, no busca información adicional.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from scripts.utils.llm_client import LLMClient
from scripts.utils.validators import validate_json_output
from scripts.utils.cleaners import cleaner

logger = logging.getLogger("auka.estructurador")


class StructurerAgent:
    """
    Agente Estructurador: Extrae información comercial de texto crudo.
    Output: JSON estandarizado para el Analista.
    """
    
    SYSTEM_PROMPT = """
    Eres AUKA-ESTRUCTURADOR. Extrae información comercial estructurada de texto crudo.
    
    CATEGORÍAS: deportivo, corporativo, social, cultural, gastronomico, religioso, otro
    REGLAS:
    1. NUNCA inventes datos - usa null si no existe
    2. SIEMPRE devuelve JSON válido
    3. confianza=alta si hay empresa+evento+contacto
    4. completo=true si hay empresa+contacto
    """
    
    OUTPUT_FIELDS = [
        "empresa", "evento", "tipo_evento", "fecha", "ubicacion",
        "ciudad", "telefono", "email", "instagram", "web",
        "confianza", "completo"
    ]
    
    def __init__(self):
        self.llm = LLMClient(primary_model="gemma-4b", backup_model="kimi-k2.5")
    
    async def structure(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estructurar datos crudos en JSON limpio.
        
        Pipeline: LIMPIAR → EXTRAER LLM → VALIDAR → DETERMINAR ACCIÓN
        """
        source = input_data.get("source", "unknown")
        raw_data = input_data.get("raw_data", {})
        
        logger.info(f"[ESTRUCTURADOR] Procesando: {source}")
        
        # 1. LIMPIAR
        cleaned_text = self._clean_raw_data(raw_data, source)
        
        # 2. EXTRAER CON LLM
        extracted = await self._extract_with_llm(cleaned_text, source)
        
        # 3. VALIDAR
        validated = self._validate_output(extracted)
        
        # 4. DETERMINAR ACCIÓN
        action = self._determine_action(validated)
        
        result = {**validated, "_metadata": {
            "source": source,
            "processed_at": datetime.utcnow().isoformat(),
            "action": action,
            "raw_text_length": len(cleaned_text)
        }}
        
        logger.info(f"[ESTRUCTURADOR] confianza={result.get('confianza')}, completo={result.get('completo')}")
        return result
    
    def _clean_raw_data(self, raw_data: Dict, source: str) -> str:
        """Limpiar datos crudos según fuente."""
        if source == "google_maps":
            parts = []
            for key in ["empresa", "direccion", "telefono", "web", "title", "address", "phone", "website"]:
                if raw_data.get(key):
                    parts.append(f"{key}: {raw_data[key]}")
            text = " | ".join(parts) if parts else str(raw_data)
            
        elif source == "instagram":
            parts = [raw_data.get("bio", "")]
            posts = raw_data.get("posts", [])
            for post in posts[:5]:
                if isinstance(post, dict) and post.get("caption"):
                    parts.append(post["caption"])
            text = "\n---\n".join(parts)
            
        else:
            text = raw_data.get("html", "") or raw_data.get("text_content", "") or str(raw_data)
        
        return cleaner.clean(text)
    
    async def _extract_with_llm(self, text: str, source: str) -> Dict:
        """Extraer entidades usando LLM."""
        model = "kimi-k2.5" if len(text) > 1000 else "gemma-4b"
        text_truncated = text[:3000] if len(text) > 3000 else text
        
        prompt = f"""
        Extrae información comercial del texto. Fuente: {source}
        
        Texto:
        ---
        {text_truncated}
        ---
        
        Devuelve SOLO JSON:
        {{
            "empresa": "nombre organizadora o null",
            "evento": "nombre evento o null",
            "tipo_evento": "deportivo/corporativo/social/cultural/gastronomico/religioso/otro o null",
            "fecha": "YYYY-MM-DD o null",
            "ubicacion": "lugar específico o null",
            "ciudad": "Caracas/Valencia/Maracay/La Guaira o null",
            "telefono": "número o null",
            "email": "correo o null",
            "instagram": "@usuario o null",
            "web": "URL o null",
            "confianza": "alta/media/baja",
            "completo": true/false
        }}
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt=self.SYSTEM_PROMPT, model=model)
            extracted = validate_json_output(response)
            for field in self.OUTPUT_FIELDS:
                if field not in extracted:
                    extracted[field] = None
            return extracted
        except Exception as e:
            logger.error(f"[ESTRUCTURADOR] Error LLM: {e}")
            return {f: None for f in self.OUTPUT_FIELDS} | {"confianza": "baja", "completo": False}
    
    def _validate_output(self, data: Dict) -> Dict:
        """Validar y corregir output."""
        for field in self.OUTPUT_FIELDS:
            if field not in data or data[field] in ["", "null", "desconocido", "unknown"]:
                data[field] = None
        
        if not data.get("ciudad") and data.get("ubicacion"):
            data["ciudad"] = self._infer_city(data["ubicacion"])
        
        if data.get("confianza") not in ["alta", "media", "baja"]:
            data["confianza"] = self._calculate_confidence(data)
        
        if not isinstance(data.get("completo"), bool):
            has_empresa = bool(data.get("empresa"))
            has_contacto = bool(data.get("telefono") or data.get("email") or data.get("instagram"))
            data["completo"] = has_empresa and has_contacto
        
        return data
    
    def _determine_action(self, data: Dict) -> str:
        """Determinar acción según confianza."""
        confianza = data.get("confianza", "baja")
        if confianza == "alta":
            return "guardar"
        elif confianza == "media":
            data["estado"] = "enriquecer"
            return "guardar_con_flag"
        return "descartar"
    
    def _infer_city(self, ubicacion: str) -> Optional[str]:
        """Inferir ciudad desde ubicación."""
        cities = ["caracas", "valencia", "maracay", "la guaira"]
        ub_lower = ubicacion.lower()
        for city in cities:
            if city in ub_lower:
                return city.title()
        if any(x in ub_lower for x in ["distrito capital", "chacao", "baruta"]):
            return "Caracas"
        if any(x in ub_lower for x in ["carabobo", "naguanagua", "san diego"]):
            return "Valencia"
        return None
    
    def _calculate_confidence(self, data: Dict) -> str:
        """Calcular confianza basada en datos presentes."""
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
        return "baja"


# Instancia singleton
structurer_agent = StructurerAgent()
