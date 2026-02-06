# src/handlers/word_game_handlers.py
from telegram import Update
from telegram.ext import ContextTypes

from src.config import settings
from src.managers import user_manager
from src.managers import word_game_manager

async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    if update.effective_user is None or update.effective_user.is_bot:
        return

    # Solo jugamos en grupos
    if update.effective_chat is None or update.effective_chat.type not in ("group", "supergroup"):
        return

    message_text = update.message.text

    if not word_game_manager.is_correct_guess(message_text):
        return

    user = update.effective_user
    user_manager.update_user_activity(user)
    total_points = user_manager.add_points(user.id, settings.WORD_GAME_POINTS)

    word = word_game_manager.get_current_word() or ""
    word_game_manager.finish_round()

    try:
        await update.message.reply_text(
            f"✅ ¡{user.first_name} ha acertado la palabra '{word}'!\n"
            f"Gana {settings.WORD_GAME_POINTS} puntos. Total: {total_points}"
        )
    except Exception as e:
        print(f"🚨 Error anunciando ganador del juego: {e}")
