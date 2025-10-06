# main.py
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
import datetime

# Importamos desde nuestra nueva estructura en 'src'
from src.config import settings
from src.managers import agenda_manager, user_manager
from src.handlers import general_handlers, agenda_handlers, group_handlers

async def track_activity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user:
        user_manager.update_user_activity(update.effective_user)

async def main() -> None:
    """
    Función principal que configura y ejecuta el bot de forma asíncrona.
    """
    agenda_manager.cargar_agenda()
    user_manager.load_users()

    app = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
    
    job_queue = app.job_queue
    job_queue.run_daily(user_manager.check_inactivity_job, time=datetime.time(hour=4, minute=0, second=0))

    # --- Registrar Handlers ---
    app.add_handler(CommandHandler("start", general_handlers.start))
    app.add_handler(CommandHandler("agenda", agenda_handlers.agenda_menu))
    app.add_handler(CommandHandler("get_group_id", group_handlers.get_group_id_command))
    app.add_handler(CallbackQueryHandler(agenda_handlers.main_agenda_callback_handler))

    # --- CAMBIO CLAVE: Quitamos /ia y añadimos el manejador de menciones ---
    # app.add_handler(CommandHandler("ia", general_handlers.ask_gemini)) # <-- LÍNEA ELIMINADA
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, general_handlers.handle_mention), group=1)
    # --------------------------------------------------------------------

    app.add_handler(MessageHandler(filters.ALL, track_activity_handler), group=2)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, agenda_handlers.manejar_mensajes_de_texto), group=3)
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, general_handlers.saludar_nuevo_miembro), group=3)

    print("🤖 Bot modular arrancado. Escuchando menciones...")
    
    async with app:
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🔌 Bot detenido limpiamente.")