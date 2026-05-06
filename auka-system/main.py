"""
AUKA System v2.0 - Sistema Autónomo de Prospección B2B para Aguas Arauka
Punto de entrada principal

Autor: Sistema de Agentes Autónomos
Fecha: 2026-05-06
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Crear directorios necesarios ANTES de configurar logging
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Configurar logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'logs/auka_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)

logger = logging.getLogger("auka.main")

# Importar agentes
from scripts.agents.director import director_agent
from scripts.agents.explorer import explorer_agent
from scripts.agents.scraper import scraper_agent
from scripts.agents.structurer import structurer_agent
from scripts.agents.analyst import analyst_agent
from scripts.agents.memory import memory_agent
from scripts.agents.conversational import conversational_agent


class AUKASystem:
    """
    Sistema AUKA - Coordinador principal.
    Inicializa y gestiona todos los agentes del ecosistema.
    """
    
    VERSION = "2.0"
    AGENTS = [
        "AUKA-DIRECTOR",
        "AUKA-EXPLORADOR", 
        "AUKA-SCRAPER",
        "AUKA-ESTRUCTURADOR",
        "AUKA-ANALISTA",
        "AUKA-MEMORIA",
        "AUKA-CONVERSACIONAL"
    ]
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.agent_status = {agent: "ready" for agent in self.AGENTS}
        logger.info(f"🚀 AUKA System v{self.VERSION} - Inicializando...")
    
    def status(self) -> dict:
        """Obtener estado actual del sistema."""
        uptime = datetime.utcnow() - self.start_time
        return {
            "version": self.VERSION,
            "status": "operational",
            "uptime_seconds": uptime.total_seconds(),
            "agents": self.agent_status,
            "agents_ready": sum(1 for s in self.agent_status.values() if s == "ready")
        }
    
    async def process_request(self, user_input: str, user_id: str = "default", canal: str = "api") -> dict:
        """
        Procesar una solicitud de usuario a través del sistema completo.
        
        Pipeline:
            Conversacional → Director → [Memoria → Explorador → Scraper → 
            Estructurador → Analista] → Memoria → Supabase → Conversacional
        """
        logger.info(f"📥 Solicitud recibida: '{user_input[:80]}...'")
        
        try:
            # 1. Conversacional clasifica y decide
            conv_result = await conversational_agent.process_message({
                "canal": canal,
                "user_id": user_id,
                "mensaje": user_input,
                "contexto": []
            })
            
            # Si es consulta simple a DB, ya está resuelta
            if conv_result.get("accion_ejecutada") == "consulta":
                return conv_result
            
            # Si requiere acción del sistema, delegar al Director
            if conv_result.get("accion_ejecutada") == "confirmacion_busqueda":
                # En implementación real, esperar confirmación del usuario
                # Por ahora, auto-confirmar para el flujo
                pass
            
            # 2. Director planifica
            director_result = await director_agent.process({
                "type": "user",
                "content": user_input,
                "context": {"user_id": user_id, "canal": canal},
                "memory": await memory_agent.get_context("last_24h")
            })
            
            # 3. Ejecutar pipeline según plan del Director
            results = await self._execute_pipeline(director_result)
            
            # 4. Formatear respuesta final
            final_response = await conversational_agent.process_message({
                "canal": canal,
                "user_id": user_id,
                "mensaje": f"FORMATEAR_RESULTADOS: {len(results)} prospectos encontrados",
                "contexto": [],
                "resultados_raw": results
            })
            
            return final_response
            
        except Exception as e:
            logger.error(f"❌ Error procesando solicitud: {e}", exc_info=True)
            return {
                "respuesta_texto": "Lo siento, ocurrió un error procesando tu solicitud. "
                                  "El equipo técnico ha sido notificado.",
                "accion_ejecutada": "error",
                "error": str(e)
            }
    
    async def _execute_pipeline(self, director_plan: dict) -> list:
        """Ejecutar el pipeline de agentes según el plan del Director."""
        all_results = []
        actions = director_plan.get("actions", [])
        
        for action in actions:
            agent_name = action.get("agent")
            task = action.get("task")
            params = action.get("params", {})
            
            logger.info(f"▶️ Ejecutando: {agent_name}.{task}")
            
            try:
                if agent_name == "memoria":
                    if task == "get_context":
                        result = await memory_agent.get_context(params.get("scope", "last_24h"))
                    elif task == "check_duplicate":
                        result = await memory_agent.check_duplicate(params)
                    elif task == "log_search":
                        result = await memory_agent.log_search(**params)
                    elif task == "mark_processed":
                        result = await memory_agent.mark_processed(params.get("empresa_id"))
                    else:
                        result = {"status": "unknown_task"}
                
                elif agent_name == "explorador":
                    result = await explorer_agent.generate_queries(params)
                
                elif agent_name == "scraper":
                    result = await scraper_agent.execute({"task": task, "params": params})
                
                elif agent_name == "estructurador":
                    result = await structurer_agent.structure(params)
                
                elif agent_name == "analista":
                    if task == "evaluate_batch":
                        result = await analyst_agent.evaluate_batch(params.get("prospectos", []))
                    else:
                        result = await analyst_agent.evaluate(params)
                
                elif agent_name == "conversacional":
                    result = await conversational_agent.process_message(params)
                
                else:
                    result = {"status": "error", "message": f"Agente desconocido: {agent_name}"}
                
                all_results.append({
                    "agent": agent_name,
                    "task": task,
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"❌ Error en {agent_name}.{task}: {e}")
                all_results.append({
                    "agent": agent_name,
                    "task": task,
                    "error": str(e)
                })
        
        return all_results
    
    async def run_scheduled_scan(self):
        """Ejecutar búsqueda programada (cada 6 horas)."""
        logger.info("⏰ Iniciando búsqueda programada...")
        
        ciudades = ["Caracas", "Valencia", "Maracay", "La Guaira"]
        objetivos = ["eventos", "empresas"]
        
        for ciudad in ciudades:
            for objetivo in objetivos:
                await self.process_request(
                    f"Buscar {objetivo} en {ciudad}",
                    user_id="system",
                    canal="scheduled"
                )
        
        logger.info("✅ Búsqueda programada completada")


# Instancia global
auka_system = AUKASystem()


async def main():
    """Función principal de entrada."""
    import os
    
    # Crear directorio de logs si no existe
    os.makedirs("logs", exist_ok=True)
    
    # Mostrar estado inicial
    status = auka_system.status()
    logger.info(f"✅ Sistema listo: {status['agents_ready']}/{len(status['agents'])} agentes activos")
    
    # En producción, aquí se iniciarían:
    # - Bot de Telegram (polling/webhook)
    # - Servidor API (FastAPI/Flask)
    # - Scheduler para búsquedas automáticas
    
    # Modo demo: procesar un comando de prueba
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
        result = await auka_system.process_request(command)
        print("\n" + "="*60)
        print("RESULTADO:")
        print("="*60)
        print(result.get("respuesta_texto", "Sin respuesta"))
    else:
        print("\n" + "="*60)
        print("AUKA System v2.0 - Modo Interactivo")
        print("Escribe 'salir' para terminar")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = input("👤 Tú: ").strip()
                if user_input.lower() in ["salir", "exit", "quit"]:
                    break
                if not user_input:
                    continue
                
                result = await auka_system.process_request(user_input)
                print(f"\n🤖 AUKA: {result.get('respuesta_texto', 'Sin respuesta')}\n")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
        
        print("\n👋 Hasta luego!")


if __name__ == "__main__":
    asyncio.run(main())
