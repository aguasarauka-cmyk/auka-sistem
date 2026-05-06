"""
AUKA-CONVERSACIONAL: Interfaz humana del sistema.
Canales: Telegram + Dashboard
Principio: Interpreta, consulta y delega. Nunca ejecuta directamente.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import os

from scripts.utils.llm_client import LLMClient
from scripts.utils.validators import validate_json_output
from scripts.database.supabase_client import db

# Intentar cargar la base de conocimiento
KNOWLEDGE_BASE = ""
try:
    kb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs", "knowledge_base.txt")
    if os.path.exists(kb_path):
        with open(kb_path, "r", encoding="utf-8") as f:
            KNOWLEDGE_BASE = f.read()
except Exception as e:
    pass

logger = logging.getLogger("auka.conversacional")


class ConversationalAgent:
    """
    Agente Conversacional: Punto de entrada humano al sistema.
    Clasifica intenciones y enruta al agente correcto.
    """
    
    SYSTEM_PROMPT = """
    Eres AUKA-CONVERSACIONAL, interfaz del sistema de prospección de Aguas Arauka.
    REGLAS:
    1. Responde SIEMPRE en español
    2. Sé claro, directo y útil
    3. NO inventes datos
    4. Confirma antes de acciones importantes
    5. Tono profesional pero conversacional
    """
    
    MENSAJE_AYUDA = """
¡Hola! Soy AUKA, tu asistente de prospección para Aguas Arauka. Puedo ayudarte con:

🔍 BUSCAR
• "busca eventos en Caracas"
• "encuentra empresas en Valencia"

📊 CONSULTAR
• "dame los prospectos de hoy"
• "muéstrame los de alta prioridad"

📈 ESTADÍSTICAS
• "resumen de hoy"
• "cuántas búsquedas hice esta semana"

✏️ ACTUALIZAR
• "marca XYZ como contactada"

Escribe en lenguaje natural. ¡Estoy listo!
"""
    
    def __init__(self):
        self.llm = LLMClient(primary_model="nvidia-kimi-k26", backup_model="llama-3.1-70b")
        if KNOWLEDGE_BASE:
            self.SYSTEM_PROMPT += f"\n\nBASE DE CONOCIMIENTO DE LA EMPRESA:\n{KNOWLEDGE_BASE}"
    
    async def process_message(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesar mensaje del usuario.
        Pipeline: CLASIFICAR → EJECUTAR → FORMATEAR
        """
        canal = input_data.get("canal", "telegram")
        mensaje = input_data.get("mensaje", "")
        user_id = input_data.get("user_id", "")
        
        logger.info(f"[CONVERSACIONAL] {canal}: {mensaje[:50]}")
        
        # 1. CLASIFICAR
        intencion = await self._clasificar_intencion(mensaje)
        
        # 2. EJECUTAR
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
            result = await self._handle_generico(mensaje, canal)
        
        # 3. FORMATEAR
        return self._format_response(result, canal)
    
    async def _clasificar_intencion(self, mensaje: str) -> str:
        """Clasificar intención con LLM."""
        prompt = f"""
        Clasifica en UNA categoría:
        CONSULTA_DB, ACTIVAR_BUSQUEDA, CAMBIAR_ESTADO, RESUMEN, AYUDA, OTRO
        
        Mensaje: "{mensaje}"
        Responde SOLO la categoría.
        """
        try:
            response = await asyncio.to_thread(self.llm.generate, prompt, system_prompt=self.SYSTEM_PROMPT)
            intencion = response.strip().upper().split()[0]
            validas = ["CONSULTA_DB", "ACTIVAR_BUSQUEDA", "CAMBIAR_ESTADO", "RESUMEN", "AYUDA", "OTRO"]
            return intencion if intencion in validas else "OTRO"
        except Exception:
            return "OTRO"
    
    async def _handle_consulta(self, mensaje: str, canal: str) -> Dict:
        """Consultar base de datos."""
        filtros = await self._extraer_filtros(mensaje)
        
        try:
            query = db.table("prospectos").select("*")
            if filtros.get("ciudad"):
                query = query.eq("ciudad", filtros["ciudad"])
            if filtros.get("prioridad"):
                query = query.eq("prioridad", filtros["prioridad"])
            if filtros.get("tipo_evento"):
                query = query.eq("tipo_evento", filtros["tipo_evento"])
            
            resultados = query.limit(20).execute()
            return {"tipo": "consulta", "datos": resultados.data or [], "filtros": filtros}
        except Exception as e:
            return {"tipo": "error", "mensaje": f"Error consultando: {e}"}
    
    async def _extraer_filtros(self, mensaje: str) -> Dict:
        """Extraer filtros del mensaje."""
        prompt = f"""
        Extrae filtros del mensaje. Devuelve JSON: {{"ciudad": "...", "prioridad": "...", "tipo_evento": "..."}}
        Ciudades: Caracas, Valencia, Maracay, La Guaira
        Prioridades: ALTA, MEDIA, BAJA
        Tipos: deportivo, corporativo, social, cultural, gastronomico, religioso
        Mensaje: "{mensaje}"
        """
        try:
            response = await asyncio.to_thread(self.llm.generate, prompt)
            return validate_json_output(response)
        except Exception:
            return {}
    
    async def _handle_busqueda(self, mensaje: str, canal: str, user_id: str) -> Dict:
        """Activar búsqueda."""
        prompt = f"""
        Extrae objetivo y ciudad: {{"objetivo": "...", "ciudad": "..."}}
        Mensaje: "{mensaje}"
        """
        try:
            response = await asyncio.to_thread(self.llm.generate, prompt)
            params = validate_json_output(response)
        except Exception:
            params = {"objetivo": "eventos", "ciudad": "Caracas"}
        
        return {
            "tipo": "confirmacion_busqueda",
            "mensaje": f"Voy a buscar {params.get('objetivo', 'eventos')} en {params.get('ciudad', 'Caracas')}. ¿Confirmas? (sí/no)",
            "params": params
        }
    
    async def _handle_update(self, mensaje: str, canal: str) -> Dict:
        return {"tipo": "update", "mensaje": "Función de actualización disponible en dashboard."}
    
    async def _handle_resumen(self, canal: str) -> Dict:
        try:
            hoy = datetime.now().strftime("%Y-%m-%d")
            prospectos = db.table("prospectos").select("count", count="exact").execute()
            hoy_p = db.table("prospectos").select("count", count="exact").gte("creado_en", hoy).execute()
            
            return {
                "tipo": "resumen",
                "datos": {
                    "total": getattr(prospectos, 'count', 0),
                    "nuevos_hoy": getattr(hoy_p, 'count', 0),
                    "fecha": hoy
                }
            }
        except Exception as e:
            return {"tipo": "error", "mensaje": str(e)}
    
    def _handle_ayuda(self, canal: str) -> Dict:
        return {"tipo": "ayuda", "mensaje": self.MENSAJE_AYUDA}
    
    async def _handle_generico(self, mensaje: str, canal: str) -> Dict:
        prompt = f"""
        Responde útil y conciso (1-2 oraciones). Si no entiendes, pide aclaración.
        Mensaje: "{mensaje}"
        """
        try:
            response = await asyncio.to_thread(self.llm.generate, prompt, system_prompt=self.SYSTEM_PROMPT)
            return {"tipo": "generico", "mensaje": response.strip()}
        except Exception:
            return {"tipo": "error", "mensaje": "No pude procesar tu mensaje. Escribe 'ayuda' para ver opciones."}
    
    def _format_response(self, result: Dict, canal: str) -> Dict[str, Any]:
        """Formatear respuesta según canal."""
        tipo = result.get("tipo", "")
        
        if tipo == "consulta":
            texto = self._format_prospectos(result.get("datos", []), result.get("total", 0), canal)
        elif tipo == "resumen":
            d = result.get("datos", {})
            texto = f"📊 Resumen ({d.get('fecha', 'hoy')}):\n• Total prospectos: {d.get('total', 0)}\n• Nuevos hoy: {d.get('nuevos_hoy', 0)}"
        elif tipo == "ayuda":
            texto = result["mensaje"]
        elif tipo == "confirmacion_busqueda":
            texto = result["mensaje"]
        elif tipo == "generico":
            texto = result["mensaje"]
        else:
            texto = result.get("mensaje", "No entendí. Escribe 'ayuda' para ver opciones.")
        
        return {
            "respuesta_texto": texto,
            "accion_ejecutada": tipo or "none",
            "datos": result.get("datos") or result.get("params"),
            "canal": canal,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _format_prospectos(self, prospectos: List[Dict], total: int, canal: str) -> str:
        """Formatear lista de prospectos."""
        if not prospectos:
            return "No encontré prospectos con esos filtros."
        
        if canal == "telegram":
            texto = f"Encontré {len(prospectos)} prospectos:\n\n"
            for i, p in enumerate(prospectos[:5], 1):
                texto += f"{i}. *{p.get('empresa', 'Sin nombre')}*\n"
                if p.get("evento"):
                    texto += f"   📅 {p['evento']}\n"
                if p.get("telefono"):
                    texto += f"   📞 {p['telefono']}\n"
                texto += f"   📍 {p.get('ciudad', '?')} | Score: {p.get('score', '?')}\n\n"
            if len(prospectos) > 5:
                texto += f"...y {len(prospectos) - 5} más en el dashboard"
            return texto
        else:
            import json
            return json.dumps(prospectos, ensure_ascii=False, indent=2)


# Instancia singleton
conversational_agent = ConversationalAgent()
