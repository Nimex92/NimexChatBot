# src/managers/group_manager.py
from telegram import Update
from telegram.ext import ContextTypes

def get_group_id(update: Update) -> int | None:
    """
    Obtiene el ID del grupo desde donde se envía el mensaje.
    """
    chat = update.effective_chat
    if chat and chat.type in ['group', 'supergroup']:
        return chat.id
    return None
