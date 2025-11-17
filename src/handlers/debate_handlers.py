# src/handlers/debate_handlers.py
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus
from src.managers import debate_manager
from src.config import settings

async def force_debate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for the /debate command. Forces a new debate.
    Only administrators can use this command.
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if the command is used in the main group
    if chat_id != settings.GROUP_CHAT_ID:
        await update.message.reply_text("Este comando solo se puede usar en el grupo principal.")
        return

    # Check if the user is an administrator
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await update.message.reply_text("⚠️ Solo los administradores pueden usar este comando.")
            return
    except Exception as e:
        print(f"Error al verificar el estado del miembro del chat: {e}")
        await update.message.reply_text("No pude verificar si eres administrador. Inténtalo de nuevo.")
        return

    await update.message.reply_text("✅ Entendido. Forzando un nuevo debate...")

    # Unpin the previous debate
    await debate_manager.unpin_previous_debate(context.bot, chat_id)

    # Send and pin the new debate
    response_message = await debate_manager.send_and_pin_debate(context.bot, chat_id)
    
    # Send a final confirmation
    await update.message.reply_text(response_message)
