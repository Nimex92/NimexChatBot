# src/handlers/group_handlers.py
from telegram import Update
from telegram.ext import ContextTypes
from src.managers import group_manager

async def get_group_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando para obtener y mostrar el ID del grupo actual.
    """
    group_id = group_manager.get_group_id(update)
    if group_id:
        await update.message.reply_text(f"El ID de este grupo es: `{group_id}`", parse_mode='MarkdownV2')
    else:
        await update.message.reply_text("Este comando solo se puede usar en un grupo.")
