# main.py
import asyncio
from telegram import Update # <-- AÑADE ESTA LÍNEA
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
import datetime
# Importamos desde nuestra nueva estructura en 'src'
from src.config import settings
from src.managers import agenda_manager, user_manager
from src.handlers import general_handlers, agenda_handlers

async def track_activity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Un handler simple que solo registra la actividad del usuario."""
    if update.effective_user:
        user_manager.update_user_activity(update.effective_user)
    # Este handler no necesita responder, así que no hacemos nada más.



def main():
    # Cargar datos al iniciar
    agenda_manager.cargar_agenda()
    user_manager.load_users()

    # Construir la aplicación del bot
    app = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
    
    # --- TAREA PROGRAMADA ---
    job_queue = app.job_queue
    # Programamos la tarea para que se ejecute todos los días a las 04:00 AM (hora del servidor)
    job_queue.run_daily(user_manager.check_inactivity_job, time=datetime.time(hour=4, minute=0, second=0))
    # ------------------------

    # --- Registrar Handlers ---
    # Handlers de comandos (prioridad 0)
    app.add_handler(CommandHandler("start", general_handlers.start))
    app.add_handler(CommandHandler("agenda", agenda_handlers.agenda_menu))
    app.add_handler(CommandHandler("ia", general_handlers.ask_gemini))
    app.add_handler(CallbackQueryHandler(agenda_handlers.main_agenda_callback_handler))

    # Handler para registrar actividad (prioridad 1)
    # Captura CUALQUIER tipo de update y actualiza la BBDD de usuarios
    app.add_handler(MessageHandler(filters.ALL, track_activity_handler), group=1)

    # Handlers de mensajes de texto específicos (prioridad 2)
    # Se ejecutan después del tracker de actividad
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, agenda_handlers.manejar_mensajes_de_texto), group=2)
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, general_handlers.saludar_nuevo_miembro), group=2)

    # Iniciar el bot
    print("🤖 Bot modular arrancado con módulo de usuarios. ¡A organizar!")
    app.run_polling()

if __name__ == "__main__":
    main()