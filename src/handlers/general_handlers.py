# src/handlers/general_handlers.py
from telegram import Update
from telegram.ext import ContextTypes
from src.managers import ai_manager

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    nombre = user.first_name or "amigo"
    saludo = (
        f"👋 ¡Hola, [{nombre}](tg://user?id={user.id})! Soy tu asistente para organizar eventos.\n\n"
        "Usa el comando /agenda para empezar a gestionar quedadas."
    )
    await update.message.reply_text(saludo, parse_mode="Markdown")

async def saludar_nuevo_miembro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Da la bienvenida a los nuevos miembros que se unen al chat."""
    for nuevo_miembro in update.message.new_chat_members:
        nombre = nuevo_miembro.first_name or "colega"
        saludo = (
            f"¡Bienvenido al grupo, {nombre}! 👋\n"
            "Soy el bot asistente. Usa /agenda para ver o crear nuevos planes."
        )
        await update.message.reply_text(saludo)

async def ask_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Toma el mensaje del usuario, se lo pasa a Gemini y responde.
    """
    user_id = update.effective_user.id
    prompt = " ".join(context.args)

    if not prompt:
        await update.message.reply_text("Dime qué necesitas después del comando. Por ejemplo:\n`/ia crea un evento mañana a las 21:00 para cenar`")
        return

    await update.message.chat.send_action('typing')
    response_text = await ai_manager.process_user_prompt(prompt, user_id)
    await update.message.reply_text(response_text)