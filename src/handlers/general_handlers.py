# src/handlers/general_handlers.py
from telegram import Update
from telegram.ext import ContextTypes

# Importamos los managers que vamos a usar en este archivo
from src.managers import ai_manager, user_manager, verification_manager
from src.config import settings

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
    """Da la bienvenida a los nuevos miembros e inicia el proceso de verificación."""
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
            f"⚠️ *IMPORTANTE*: Tienes *{settings.PRESENTATION_TIMEOUT_MINUTES} minutos* para presentarte brevemente al grupo.\n"
            "Cuéntanos quién eres, qué te trae por aquí o saluda con gracia.\n"
            "Si no lo haces, tendré que darte un toque... ¡y luego la patada! 👢\n\n"
            "¡Dale, no seas tímido!"
        )
        await update.message.reply_text(saludo, parse_mode="Markdown")

async def check_presentation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Analiza los mensajes de usuarios pendientes de verificación.
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

    # Usamos la IA para evaluar si es una presentación válida
    es_valido = await ai_manager.evaluate_presentation(message_text)

    if es_valido:
        # 1. Marcar como verificado
        user_manager.set_user_status(user.id, "verified")
        
        # 2. Cancelar jobs de advertencia/baneo
        verification_manager.cancel_verification_jobs(context, user.id)
        
        # 3. Felicitar
        await update.message.reply_text(
            f"¡Genial, {user.first_name}! Presentación aceptada. ✅\n"
            "Ya eres uno de los nuestros. ¡Bienvenido oficialmente! 🎉"
        )
    else:
        # Si no es válido, no hacemos nada. Dejamos que el reloj siga corriendo.
        # Opcionalmente, podríamos dar feedback, pero puede ser molesto si solo están charlando.
        pass

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