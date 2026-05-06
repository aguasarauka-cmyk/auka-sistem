"""
AUKA - Telegram Bot v2.0
Bot completo con búsqueda real, feedback en tiempo real,
confirmaciones y gestión de prospectos.
"""

import logging
import sys
import os
import asyncio
import json

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, filters
)
from config.settings import settings
from scripts.agents.conversational import conversational_agent
from scripts.database.supabase_client import db

logging.basicConfig(
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'logs/telegram_bot.log')
    ]
)
logger = logging.getLogger("auka.telegram_bot")

# Estado de confirmaciones pendientes por usuario
pending_confirmations = {}


def is_allowed(user_id: int) -> bool:
    if not settings.ALLOWED_TELEGRAM_USERS:
        return True
    return user_id in settings.ALLOWED_TELEGRAM_USERS


async def safe_send(context, chat_id, text, parse_mode="Markdown"):
    """Enviar mensaje con fallback si Markdown falla."""
    try:
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    except Exception:
        # Fallback sin formato
        clean = text.replace("*", "").replace("_", "").replace("`", "")
        try:
            await context.bot.send_message(chat_id=chat_id, text=clean)
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")


# ═══════════════════════════════════════════════════════════════
# COMANDOS
# ═══════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await safe_send(context, update.effective_chat.id, "⛔ Acceso denegado.")
        return
    
    text = (
        "🚀 *AUKA System* — Tu asistente de prospección para Aguas Arauka\n\n"
        "Puedo ayudarte a:\n"
        "🔍 Buscar eventos y empresas en Google Maps\n"
        "📊 Consultar prospectos guardados\n"
        "📈 Ver estadísticas del sistema\n\n"
        "*Comandos:*\n"
        "🔹 /buscar [ciudad] — Buscar prospectos\n"
        "🔹 /prospectos — Ver últimos prospectos\n"
        "🔹 /alta\\_prioridad — Solo alta prioridad\n"
        "🔹 /stats — Estadísticas\n"
        "🔹 /help — Esta ayuda\n\n"
        "💬 También puedes escribir en lenguaje natural:\n"
        "• _\"busca eventos deportivos en Caracas\"_\n"
        "• _\"dame prospectos de Valencia\"_\n"
        "• _\"resumen de hoy\"_"
    )
    await safe_send(context, update.effective_chat.id, text)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, context)


async def cmd_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    
    ciudad = " ".join(context.args) if context.args else "Caracas"
    query = "productoras de eventos"
    
    await safe_send(
        context, update.effective_chat.id,
        f"¿Quieres que busque *{query}* en *{ciudad}*? Responde *sí* para confirmar o *no* para cancelar."
    )
    
    pending_confirmations[str(update.effective_user.id)] = {
        "action": "search",
        "city": ciudad,
        "query": query
    }


async def cmd_prospectos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        prospectos = await db.get_prospectos(limit=10)
        if not prospectos:
            await safe_send(context, chat_id, "📭 No hay prospectos aún. Usa /buscar para empezar.")
            return
        
        text = f"📊 *Últimos {len(prospectos)} prospectos:*\n\n"
        for i, p in enumerate(prospectos[:10], 1):
            empresa = p.get('empresa', 'Sin nombre')
            ciudad = p.get('ciudad', '?')
            telefono = p.get('telefono', '')
            prioridad = p.get('prioridad', 'BAJA')
            emoji_p = "🔴" if prioridad == "ALTA" else ("🟡" if prioridad == "MEDIA" else "🟢")
            
            text += f"{i}. {emoji_p} *{empresa}*\n"
            text += f"   📍 {ciudad}"
            if telefono:
                text += f" | 📞 {telefono}"
            text += "\n"
        
        await safe_send(context, chat_id, text)
    except Exception as e:
        logger.error(f"Error en /prospectos: {e}")
        await safe_send(context, chat_id, f"❌ Error consultando: {e}")


async def cmd_alta_prioridad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        prospectos = await db.get_prospectos(filters={"prioridad": "ALTA"}, limit=10)
        if not prospectos:
            await safe_send(context, chat_id, "No hay prospectos de alta prioridad aún.")
            return
        
        text = f"🔴 *{len(prospectos)} prospectos ALTA PRIORIDAD:*\n\n"
        for i, p in enumerate(prospectos, 1):
            text += f"{i}. *{p.get('empresa', '?')}*\n"
            if p.get('telefono'):
                text += f"   📞 {p['telefono']}\n"
            if p.get('web'):
                text += f"   🌐 {p['web']}\n"
            text += f"   📍 {p.get('ciudad', '?')} | Score: {p.get('score', 0)}\n\n"
        
        await safe_send(context, chat_id, text)
    except Exception as e:
        await safe_send(context, chat_id, f"❌ Error: {e}")


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        result = await asyncio.to_thread(
            lambda: db.table("prospectos").select("*", count="exact").execute()
        )
        total = getattr(result, 'count', 0) or len(result.data or [])
        
        # Contar por prioridad
        alta = sum(1 for p in (result.data or []) if p.get('prioridad') == 'ALTA')
        media = sum(1 for p in (result.data or []) if p.get('prioridad') == 'MEDIA')
        baja = sum(1 for p in (result.data or []) if p.get('prioridad') == 'BAJA')
        
        # Contar por ciudad
        ciudades = {}
        for p in (result.data or []):
            c = p.get('ciudad', 'Sin ciudad')
            ciudades[c] = ciudades.get(c, 0) + 1
        
        text = (
            "📈 *Estadísticas AUKA*\n\n"
            f"📊 *Total prospectos:* {total}\n"
            f"🔴 Alta prioridad: {alta}\n"
            f"🟡 Media: {media}\n"
            f"🟢 Baja: {baja}\n\n"
            "📍 *Por ciudad:*\n"
        )
        for ciudad, count in sorted(ciudades.items(), key=lambda x: -x[1]):
            text += f"  • {ciudad}: {count}\n"
        
        await safe_send(context, chat_id, text)
    except Exception as e:
        await safe_send(context, chat_id, f"❌ Error: {e}")


# ═══════════════════════════════════════════════════════════════
# BÚSQUEDA REAL CON FEEDBACK EN TIEMPO REAL
# ═══════════════════════════════════════════════════════════════
# HANDLER DE MENSAJES NATURALES
# ═══════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════
# HANDLER DE MENSAJES NATURALES
# ═══════════════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        return
    
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    user_id_str = str(user_id)
    
    # ── Chequear confirmaciones pendientes ──
    if user_id_str in pending_confirmations:
        conf = pending_confirmations[user_id_str]
        
        if text.lower() in ["sí", "si", "yes", "confirmar", "dale", "ok", "s"]:
            del pending_confirmations[user_id_str]
            await safe_send(context, chat_id, "🚀 *Iniciando pipeline de inteligencia...* Esto puede tardar entre 30 y 60 segundos.")
            
            from main import auka_system
            try:
                # Ejecutamos el pipeline completo
                result = await auka_system.process_request(
                    user_input=conf.get("original_text", text), 
                    user_id=user_id_str, 
                    canal="telegram"
                )
                
                respuesta = result.get("respuesta_texto", "Búsqueda completada sin respuesta del agente.")
                if len(respuesta) > 4000:
                    respuesta = respuesta[:4000] + "\n\n[Truncado...]"
                
                await safe_send(context, chat_id, respuesta)
            except Exception as e:
                logger.error(f"Error ejecutando pipeline: {e}")
                await safe_send(context, chat_id, "❌ Hubo un error ejecutando el pipeline de agentes.")
            return
            
        elif text.lower() in ["no", "cancelar", "cancel", "n"]:
            del pending_confirmations[user_id_str]
            await safe_send(context, chat_id, "❌ Búsqueda cancelada.")
            return

    # ── Usar el agente conversacional para el resto ──
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    input_data = {
        "canal": "telegram",
        "mensaje": text,
        "user_id": user_id_str
    }
    
    try:
        resultado = await conversational_agent.process_message(input_data)
        respuesta = resultado.get("respuesta_texto", "No entendí. Escribe /help para ver opciones.")
        
        if len(respuesta) > 4000:
            respuesta = respuesta[:4000] + "\n\n[Truncado...]"
        
        # Si el agente devuelve confirmación de búsqueda, manejar
        if resultado.get("accion_ejecutada") == "confirmacion_busqueda":
            params = resultado.get("datos", {})
            if params:
                pending_confirmations[user_id_str] = {
                    "action": "search",
                    "city": params.get("ciudad", "Caracas"),
                    "query": params.get("objetivo", "productoras de eventos"),
                    "original_text": params.get("mensaje_original", text)
                }
        
        await safe_send(context, chat_id, respuesta)
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}", exc_info=True)
        await safe_send(context, chat_id, "❌ Error procesando tu solicitud. Intenta de nuevo o escribe /help.")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN no configurado.")
        sys.exit(1)
    
    logger.info(f"🚀 Iniciando AUKA Telegram Bot v2.0")
    logger.info(f"   Modelo: Kimi K2.6 (primario) + Llama 3.1 70B (backup)")
    logger.info(f"   Usuarios permitidos: {settings.ALLOWED_TELEGRAM_USERS}")
    
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # Comandos
    application.add_handler(CommandHandler('start', cmd_start))
    application.add_handler(CommandHandler('help', cmd_help))
    application.add_handler(CommandHandler('buscar', cmd_buscar))
    application.add_handler(CommandHandler('prospectos', cmd_prospectos))
    application.add_handler(CommandHandler('alta_prioridad', cmd_alta_prioridad))
    application.add_handler(CommandHandler('stats', cmd_stats))
    
    # Mensajes naturales
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # Iniciar polling
    application.run_polling()


if __name__ == '__main__':
    main()
