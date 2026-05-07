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
    Eres AUKA, un Socio Estratégico, Arquitecto de Negocios y Operador de IA.
    Aunque administras el sistema de prospección B2B de Aguas Arauka, tienes total 
    libertad para razonar, debatir estrategias, analizar nuevos modelos de negocio, 
    gestionar infraestructura y adaptar parámetros operativos si el usuario te lo requiere.
    
    REGLAS:
    1. Responde SIEMPRE en español.
    2. Actúa como un consultor experto: profundiza y argumenta cuando se te pida análisis.
    3. Si es una orden operativa (buscar, actualizar), ejecútala velozmente. Si es un debate, abre tu contexto.
    4. NO inventes datos. Si no sabes algo, asume tu rol de IA orquestadora y propón buscarlo.
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
        Pipeline: CLASIFICAR → VALIDAR_MODO → EJECUTAR → FORMATEAR
        """
        canal = input_data.get("canal", "telegram")
        mensaje = input_data.get("mensaje", "")
        user_id = input_data.get("user_id", "")
        
        logger.info(f"[CONVERSACIONAL] {canal}: {mensaje[:50]}")
        
        # 1. CLASIFICAR
        intencion = await self._clasificar_intencion(mensaje)
        
        # 2. VALIDAR MODO DE PROSPECCIÓN (si es búsqueda)
        if intencion == "ACTIVAR_BUSQUEDA":
            modo_prospeccion = input_data.get("modo_prospeccion")
            
            # Si no viene el modo explícito, preguntar al usuario
            if not modo_prospeccion:
                modo_detectado = await self._detectar_modo_prospeccion(mensaje)
                if not modo_detectado:
                    return self._format_response({
                        "tipo": "confirmacion_modo",
                        "mensaje": "Para darte mejores resultados, ¿buscas empresas organizadoras de eventos o eventos específicos?"
                    }, canal)
                modo_prospeccion = modo_detectado
            
            result = await self._handle_busqueda(mensaje, canal, user_id, modo_prospeccion)
        elif intencion == "CONSULTA_DB":
            result = await self._handle_consulta(mensaje, canal)
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
    
    async def _detectar_modo_prospeccion(self, mensaje: str) -> Optional[str]:
        """Detecta automáticamente el modo de prospección desde el mensaje del usuario."""
        prompt = f"""
        Analiza el siguiente mensaje y determina si el usuario busca:
        - MODO_EMPRESAS: Información de empresas organizadoras de eventos (contacto, web, redes, etc.)
        - MODO_EVENTOS: Información de eventos específicos (nombre, fecha, lugar, organizador, contacto)
        
        Mensaje: "{mensaje}"
        
        Responde SOLO con "MODO_EMPRESAS", "MODO_EVENTOS" o "INDETERMINADO".
        """
        try:
            response = await asyncio.to_thread(self.llm.generate, prompt, system_prompt=self.SYSTEM_PROMPT)
            modo = response.strip().upper()
            if "MODO_EMPRESAS" in modo:
                return "MODO_EMPRESAS"
            elif "MODO_EVENTOS" in modo:
                return "MODO_EVENTOS"
            return None
        except Exception:
            return None
    
    async def _clasificar_intencion(self, mensaje: str) -> str:
        """Clasificar intención con LLM."""
        prompt = f"""
        Clasifica en UNA categoría:
        CONSULTA_DB, ACTIVAR_BUSQUEDA (incluye web scraping, escanear perfiles y visitar links), CAMBIAR_ESTADO, RESUMEN, AYUDA, ESTRATEGIA, OTRO
        
        Mensaje: "{mensaje}"
        Responde SOLO la categoría.
        """
        try:
            response = await asyncio.to_thread(self.llm.generate, prompt, system_prompt=self.SYSTEM_PROMPT)
            intencion = response.strip().upper().split()[0]
            validas = ["CONSULTA_DB", "ACTIVAR_BUSQUEDA", "CAMBIAR_ESTADO", "RESUMEN", "AYUDA", "ESTRATEGIA", "OTRO"]
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
    
    async def _handle_busqueda(self, mensaje: str, canal: str, user_id: str, modo_prospeccion: str = "MODO_EMPRESAS") -> Dict:
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
        
        # Guardar el mensaje original para que el Director tenga contexto (URLs, detalles)
        params["mensaje_original"] = mensaje
        params["modo_prospeccion"] = modo_prospeccion
        
        return {
            "tipo": "confirmacion_busqueda",
            "mensaje": f"Voy a buscar {params.get('objetivo', 'eventos')} en {params.get('ciudad', 'Caracas')}. Modo: {'Empresas' if modo_prospeccion == 'MODO_EMPRESAS' else 'Eventos'}. ¿Confirmas? (sí/no)",
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
        El usuario está planteando una duda estratégica, una configuración del sistema o una conversación profunda.
        Utiliza tu máxima capacidad analítica y responde con la profundidad, estructura y detalle necesarios. 
        Actúa como un CTO / Socio de negocios.
        
        Mensaje del usuario: "{mensaje}"
        """
        try:
            response = await asyncio.to_thread(self.llm.generate, prompt, system_prompt=self.SYSTEM_PROMPT)
            return {"tipo": "generico", "mensaje": response.strip()}
        except Exception:
            return {"tipo": "error", "mensaje": "Hubo un fallo en mi razonamiento. ¿Podrías reformular?"}
    
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
