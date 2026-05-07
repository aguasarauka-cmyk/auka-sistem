"""
AUKA - Bot de Telegram
Integración del Agente Conversacional con Telegram.
Soporta: comandos, mensajes en lenguaje natural, confirmaciones.
"""

import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    filters, ContextTypes
)

from scripts.agents.conversational import conversational_agent
from scripts.agents.memory import memory_agent
from config.settings import settings

logger = logging.getLogger("auka.telegram")


class TelegramBot:
    """Bot de Telegram para AUKA System."""
    
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.pending_confirmations = {}  # user_id → params
        self.pending_modo = {}  # user_id → modo_prospeccion
    
    async def start(self):
        """Iniciar el bot."""
        if not self.token:
            logger.error("[TELEGRAM] Token no configurado")
            return
        
        application = Application.builder().token(self.token).build()
        
        # Handlers
        application.add_handler(CommandHandler("start", self._cmd_start))
        application.add_handler(CommandHandler("help", self._cmd_help))
        application.add_handler(CommandHandler("prospectos", self._cmd_prospectos))
        application.add_handler(CommandHandler("buscar", self._cmd_buscar))
        application.add_handler(CommandHandler("stats", self._cmd_stats))
        application.add_handler(CommandHandler("alta_prioridad", self._cmd_alta_prioridad))
        
        # Mensajes generales
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        logger.info("[TELEGRAM] Bot iniciado")
        await application.initialize()
        await application.start_polling()
        await application.updater.start_polling()
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler /start."""
        await update.message.reply_text(
            "🚀 *AUKA System* - Tu asistente de prospección para Aguas Arauka\n\n"
            "Puedo ayudarte a:\n"
            "🔍 Buscar eventos y empresas\n"
            "📊 Consultar prospectos\n"
            "📈 Ver estadísticas\n\n"
            "Escribe /help para ver todos los comandos o envíame un mensaje en lenguaje natural.",
            parse_mode="Markdown"
        )
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler /help."""
        help_text = (
            "*Comandos disponibles:*\n\n"
            "🔍 *Búsqueda*\n"
            "`/buscar [ciudad]` - Buscar eventos\n"
            "Ej: `/buscar Caracas`\n\n"
            "📊 *Consultas*\n"
            "`/prospectos` - Ver últimos prospectos\n"
            "`/alta_prioridad` - Ver alta prioridad\n"
            "`/stats` - Estadísticas del sistema\n\n"
            "💬 También puedes escribir en lenguaje natural:\n"
            "• 'dame prospectos de Valencia'\n"
            "• 'busca eventos deportivos en Caracas'\n"
            "• 'cuántos leads tenemos'"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def _cmd_prospectos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler /prospectos."""
        result = await conversational_agent.process_message({
            "canal": "telegram",
            "user_id": str(update.effective_user.id),
            "mensaje": "dame los últimos prospectos",
            "contexto": []
        })
        await update.message.reply_text(result["respuesta_texto"], parse_mode="Markdown")
    
    async def _cmd_buscar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler /buscar [ciudad]."""
        ciudad = " ".join(context.args) if context.args else "Caracas"
        result = await conversational_agent.process_message({
            "canal": "telegram",
            "user_id": str(update.effective_user.id),
            "mensaje": f"busca eventos en {ciudad}",
            "contexto": []
        })
        await update.message.reply_text(result["respuesta_texto"], parse_mode="Markdown")
    
    async def _cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler /stats."""
        result = await conversational_agent.process_message({
            "canal": "telegram",
            "user_id": str(update.effective_user.id),
            "mensaje": "estadísticas del sistema",
            "contexto": []
        })
        await update.message.reply_text(result["respuesta_texto"], parse_mode="Markdown")
    
    async def _cmd_alta_prioridad(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler /alta_prioridad."""
        result = await conversational_agent.process_message({
            "canal": "telegram",
            "user_id": str(update.effective_user.id),
            "mensaje": "dame prospectos de alta prioridad",
            "contexto": []
        })
        await update.message.reply_text(result["respuesta_texto"], parse_mode="Markdown")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para mensajes en lenguaje natural."""
        mensaje = update.message.text
        user_id = str(update.effective_user.id)
        
        # Verificar pregunta de modo pendiente
        if user_id in self.pending_modo:
            modo = self._determinar_modo(mensaje)
            if modo:
                # Guardar modo y limpiar estado
                self.pending_modo[user_id] = modo
                await update.message.reply_text(
                    f"✅ Modo seleccionada: *{modo}*\n\n"
                    "Ahora confirmo: ¿busco eventos en Caracas? (sí/no)",
                    parse_mode="Markdown"
                )
                return
            elif mensaje.lower() in ["no", "cancelar"]:
                await update.message.reply_text("❌ Cancelado.")
                del self.pending_modo[user_id]
                return
        
        # Verificar confirmaciones pendientes
        if user_id in self.pending_confirmations:
            if mensaje.lower() in ["sí", "si", "yes", "confirmar", "ok", "dale"]:
                params = self.pending_confirmations[user_id]
                # Incluye el modo si estaba seleccionado
                modo = self.pending_modo.get(user_id)
                if modo:
                    params["modo_prospeccion"] = modo
                
                await update.message.reply_text("🔍 Ejecutando búsqueda... (solo Venezuela)")
                
                # Ejecutar búsqueda
                result = await conversational_agent.process_message({
                    "canal": "telegram",
                    "user_id": user_id,
                    "mensaje": f"busca en {params.get('ciudad', 'Caracas')}",
                    "contexto": [],
                    "modo_prospeccion": modo or "MODO_EMPRESAS"
                })
                
                await update.message.reply_text(result.get("respuesta_texto", "Búsqueda completada"))
                
                del self.pending_confirmations[user_id]
                if user_id in self.pending_modo:
                    del self.pending_modo[user_id]
                return
            elif mensaje.lower() in ["no", "cancelar"]:
                await update.message.reply_text("❌ Búsqueda cancelada.")
                del self.pending_confirmations[user_id]
                if user_id in self.pending_modo:
                    del self.pending_modo[user_id]
                return
        
        # Procesar con agente conversacional
        result = await conversational_agent.process_message({
            "canal": "telegram",
            "user_id": user_id,
            "mensaje": mensaje,
            "contexto": []
        })
        
        # Guardar contexto conversacional
        await memory_agent.save_conversational_context(
            user_id=user_id,
            ultimo_mensaje=mensaje,
            modo_prospeccion=result.get("params", {}).get("modo_prospeccion")
        )
        
        # Si requiere confirmación de modo, guardar
        if result.get("accion_ejecutada") == "confirmacion_modo":
            await update.message.reply_text(
                result.get("respuesta_texto", "¿Busco empresas o eventos específicos?"),
                parse_mode="Markdown"
            )
            self.pending_modo[user_id] = None  # Esperar respuesta del usuario
            return
        
        # Si requiere confirmación de búsqueda, guardar
        if result.get("accion_ejecutada") == "confirmacion_busqueda":
            self.pending_confirmations[user_id] = result.get("params", {})
            await update.message.reply_text(
                result.get("respuesta_texto", "Confirmar búsqueda (sí/no)"),
                parse_mode="Markdown"
            )
            return
        
        await update.message.reply_text(result["respuesta_texto"], parse_mode="Markdown")
    
    def _determinar_modo(self, mensaje: str) -> str:
        """Determinar modo de prospección desde la respuesta del usuario."""
        msg = mensaje.lower()
        if any(p in msg for p in ["empresa", "contacto", "proveedor", "organizadora", "agencia"]):
            return "MODO_EMPRESAS"
        elif any(p in msg for p in ["evento", "fechas", "cuándo", "cuándo es"]):
            return "MODO_EVENTOS"
        return None


# Instancia singleton
telegram_bot = TelegramBot()


async def start_bot():
    """Función de entrada para iniciar el bot."""
    await telegram_bot.start()


if __name__ == "__main__":
    asyncio.run(start_bot())
