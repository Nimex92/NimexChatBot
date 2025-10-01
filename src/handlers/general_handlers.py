# src/handlers/general_handlers.py
"""Manejadores de comandos y eventos generales del bot.

Contiene los handlers para comandos como /start, así como para eventos
generales como la bienvenida a nuevos miembros o la interacción con la IA.
"""
from telegram import Update
from telegram.ext import ContextTypes
from src.managers import ai_manager

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saluda al usuario cuando ejecuta el comando /start.

    Envía un mensaje de bienvenida personalizado mencionando al usuario
    y le da una breve instrucción sobre cómo usar el bot.

    Args:
        update (Update): El objeto de actualización de Telegram.
        context (ContextTypes.DEFAULT_TYPE): El contexto del bot.
    """
    user = update.effective_user
    nombre = user.first_name or "amigo"
    saludo = (
        f"👋 ¡Hola, [{nombre}](tg://user?id={user.id})! Soy tu asistente para organizar eventos.\n\n"
        "Usa el comando /agenda para empezar a gestionar quedadas."
    )
    await update.message.reply_text(saludo, parse_mode="Markdown")

async def saludar_nuevo_miembro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Da la bienvenida a los nuevos miembros que se unen al chat.

    Itera sobre los nuevos miembros en la actualización y envía un mensaje
    de bienvenida para cada uno, indicándoles el comando principal (/agenda).

    Args:
        update (Update): El objeto de actualización de Telegram, que contiene
            la lista de nuevos miembros del chat.
        context (ContextTypes.DEFAULT_TYPE): El contexto del bot.
    """
    for nuevo_miembro in update.message.new_chat_members:
        nombre = nuevo_miembro.first_name or "colega"
        saludo = (
            f"¡Bienvenido al grupo, {nombre}! 👋\n"
            "Soy el bot asistente. Usa /agenda para ver o crear nuevos planes."
        )
        await update.message.reply_text(saludo)

async def ask_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /ia para interactuar con el modelo de IA.

    Recoge el texto que sigue al comando /ia, lo usa como prompt y lo envía
    al `ai_manager` para ser procesado. Muestra una acción de "escribiendo"
    mientras espera la respuesta y luego envía la respuesta de la IA al chat.

    Si el comando se invoca sin texto, responde con un mensaje de ayuda.

    Args:
        update (Update): El objeto de actualización de Telegram.
        context (ContextTypes.DEFAULT_TYPE): El contexto del bot, que contiene
            los argumentos del comando.
    """
    user_id = update.effective_user.id
    prompt = " ".join(context.args)

    if not prompt:
        await update.message.reply_text("Dime qué necesitas después del comando. Por ejemplo:\n`/ia crea un evento mañana a las 21:00 para cenar`")
        return

    await update.message.chat.send_action('typing')
    response_text = await ai_manager.process_user_prompt(prompt, user_id)
    await update.message.reply_text(response_text)