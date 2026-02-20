# src/handlers/general_handlers.py
from telegram import Update
from telegram.ext import ContextTypes
import re

# Importamos los managers que vamos a usar en este archivo
from src.managers import ai_manager, user_manager, verification_manager
from src.config import settings

RULES_ACCEPTANCE_PATTERN = re.compile(r"\bacept\w*\b.*\bnorm\w*\b|\bnorm\w*\b.*\bacept\w*\b", re.IGNORECASE)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    nombre = user.first_name or "majo"
    bot_username = context.bot.username
    saludo = (
        f"¡Aúpa, [{nombre}](tg://user?id={user.id})\\! 👋 Soy Nimex, tu asistente riojano con memoria 🧠 y agenda 📅 integrada\\.\n\n"
        f"Puedes usar el comando /agenda para empezar o, si estoy en un grupo, *mencióname con @{bot_username}* y dime qué necesitas\\. Por ejemplo:\n"
        f"`@{bot_username} crea un evento para el sábado a las 20:00 para cenar`\n\n"
        "Además, estaré echando un ojo al chat para mantener el buen rollo\\. 😉\n\n"
        "¡Organízate fácil y rápido\\! 🚀"
    )
    await update.message.reply_text(saludo, parse_mode="MarkdownV2")

async def saludar_nuevo_miembro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Da la bienvenida a los nuevos miembros e inicia la aceptación de normas."""
    for nuevo_miembro in update.message.new_chat_members:
        if nuevo_miembro.is_bot:
            continue
            
        nombre = nuevo_miembro.first_name or "colega"
        user_id = nuevo_miembro.id
        chat_id = update.effective_chat.id
        
        # Iniciamos el proceso de verificación
        await verification_manager.schedule_verification_start(context, user_id, chat_id)
        
        saludo = (
            f"¡Bienvenido al grupo, {nombre}! 👋\n\n"
            "⚠️ *IMPORTANTE*: Para desbloquear las funciones del bot, acepta las normas del grupo.\n"
            "Escribe un mensaje como: *acepto las normas*.\n\n"
            f"Si pasan *{settings.PRESENTATION_TIMEOUT_MINUTES} minutos* sin hacerlo, te mandaré un recordatorio."
        )
        await update.message.reply_text(saludo, parse_mode="Markdown")

async def check_presentation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Analiza mensajes de usuarios pendientes para detectar aceptación de normas.
    """
    user = update.effective_user
    if not user or user.is_bot:
        return

    # Si el usuario ya está verificado, pasamos
    if user_manager.is_verified(user.id):
        return

    message_text = update.message.text
    if not message_text:
        return

    # Aceptación explícita de normas
    es_valido = bool(RULES_ACCEPTANCE_PATTERN.search(message_text))

    if es_valido:
        # 1. Marcar como verificado
        user_manager.set_user_status(user.id, "verified")
        
        # 2. Cancelar jobs de recordatorio
        verification_manager.cancel_verification_jobs(context, user.id)
        
        # 3. Felicitar
        await update.message.reply_text(
            f"¡Genial, {user.first_name}! Normas aceptadas. ✅\n"
            "Ya eres uno de los nuestros. ¡Bienvenido oficialmente! 🎉"
        )

async def handle_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Se activa cuando alguien menciona al bot en un grupo.
    """
    print("DEBUG: handle_mention function called.") # Temporary debug print
    # Nos aseguramos de que el mensaje no sea nulo
    if not update.message or not update.message.text:
        return

    message_text = update.message.text
    bot_username = context.bot.username
    user_id = update.effective_user.id

    # 1. Comprobamos si el bot ha sido mencionado
    if f"@{bot_username}" in message_text:
        
        # 2. Limpiamos el mensaje para quitar la mención y obtener el prompt real
        prompt = message_text.replace(f"@{bot_username}", "").strip()

        if not prompt:
            await update.message.reply_text("¡Aúpa! Dime algo más después de mencionarme, majo. 😉")
            return

        # 3. Llamamos a la IA como antes, pero respondiendo al mensaje original
        await update.message.chat.send_action('typing')
        response_text = await ai_manager.process_user_prompt(prompt, user_id)
        await update.message.reply_text(response_text, parse_mode="Markdown")
