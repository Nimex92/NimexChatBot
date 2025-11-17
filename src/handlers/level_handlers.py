# src/handlers/level_handlers.py
import random
from telegram import Update
from telegram.ext import ContextTypes
from src.managers import user_manager

# --- Mensajes de Anuncio de Subida de Nivel ---
LEVEL_UP_MESSAGES = [
    "¡Atención, cuadrilla! @{user_name} ha hablado tanto de vinos que acaba de subir al Nivel {level_num}: **{level_name}**! ¡Invítate a unos chatos, que te lo has ganado! 🍇",
    "¡Aúpa ahí! @{user_name} se ha ganado el ascenso al Nivel {level_num}: **{level_name}**. ¡Ya eres una leyenda de la Laurel! 🎉",
    "¡Qué hermosura! @{user_name} ha alcanzado el Nivel {level_num}: **{level_name}**. ¡Tu sabiduría riojana es legendaria! 🍷",
    "¡La virgen! @{user_name} no para y ya es Nivel {level_num}: **{level_name}**. ¡Siguiente parada, la Calle San Juan! 🍄",
    "¡Dale, majo/a! @{user_name} acaba de llegar al Nivel {level_num}: **{level_name}**. ¡Te estás convirtiendo en un/a riojano/a de pro! 🚀"
]

async def announce_level_up(context: ContextTypes.DEFAULT_TYPE, chat_id: int, level_up_info: dict):
    """
    Envía un mensaje público al grupo para anunciar una subida de nivel.
    """
    message_template = random.choice(LEVEL_UP_MESSAGES)
    message = message_template.format(
        user_name=level_up_info["user_name"],
        level_num=level_up_info["level_num"],
        level_name=level_up_info["level_name"]
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def level_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para el comando /nivel. Muestra al usuario su nivel y progreso.
    """
    user_id = update.effective_user.id
    level_info = user_manager.get_user_level_info(user_id)

    if not level_info:
        await update.message.reply_text("No he encontrado tus datos, ¡habla un poco para empezar a sumar experiencia!")
        return

    # --- Crear la barra de progreso ---
    xp_in_level = level_info["xp"] - level_info["xp_base_level"]
    xp_for_level = (level_info["xp_next_level"] or level_info["xp"]) - level_info["xp_base_level"]
    
    progress_percentage = 0
    if xp_for_level > 0:
        progress_percentage = (xp_in_level / xp_for_level)
    
    filled_blocks = int(progress_percentage * 10)
    empty_blocks = 10 - filled_blocks
    progress_bar = "▓" * filled_blocks + "░" * empty_blocks

    # --- Formatear el mensaje ---
    if level_info["xp_next_level"]:
        progress_text = f"{xp_in_level}/{xp_for_level} XP para el siguiente nivel."
    else:
        progress_text = "¡Has alcanzado el máximo nivel! ¡Eres una leyenda!"

    message = (
        f"📜 **Tu Senda del Riojano**\n\n"
        f"¡Aúpa, {level_info['name']}!\n\n"
        f"Tu nivel actual es:\n"
        f"**Nivel {level_info['level']}: {level_info['level_name']}**\n\n"
        f"Progreso:\n`{progress_bar}`\n"
        f"_{progress_text}_"
    )

    # Enviar como mensaje privado para no hacer spam en el grupo
    try:
        await context.bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')
        if update.effective_chat.type != 'private':
            await update.message.reply_text("🤫 Te he enviado tus progresos por privado para no dar pistas a los demás.")
    except Exception:
        await update.message.reply_text("😬 ¡Vaya! Parece que no puedo enviarte mensajes privados. ¿Has iniciado una conversación conmigo antes?")
