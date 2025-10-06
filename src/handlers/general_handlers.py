# src/handlers/general_handlers.py
from telegram import Update
from telegram.ext import ContextTypes

# Importamos los managers que vamos a usar en este archivo
from src.managers import ai_manager

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    nombre = user.first_name or "majo"
    bot_username = context.bot.username
    saludo = (
        f"¡Aúpa, [{nombre}](tg://user?id={user.id})! 👋 Soy Nimex, tu asistente riojano con memoria 🧠 y agenda 📅 integrada\.\n\n"
        f"Puedes usar el comando /agenda para empezar o, si estoy en un grupo, *mencióname con @{bot_username}* y dime qué necesitas\. Por ejemplo:\n"
        f"`@{bot_username} crea un evento para el sábado a las 20:00 para cenar`\n\n"
        "Además, estaré echando un ojo al chat para mantener el buen rollo\. 😉\n\n"
        "¡Organízate fácil y rápido! 🚀"
    )
    await update.message.reply_text(saludo, parse_mode="MarkdownV2")

async def saludar_nuevo_miembro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Da la bienvenida a los nuevos miembros que se unen al chat."""
    for nuevo_miembro in update.message.new_chat_members:
        nombre = nuevo_miembro.first_name or "colega"
        saludo = (
            f"¡Bienvenido al grupo, {nombre}! 👋\n"
            "Soy el bot asistente. Usa /agenda para ver los planes "
            "o mencióname (@{context.bot.username}) si necesitas algo."
        )
        await update.message.reply_text(saludo.format(context=context))

async def handle_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Se activa cuando alguien menciona al bot en un grupo.
    """
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