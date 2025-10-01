"""Punto de entrada principal para la aplicación del bot de Telegram.

Este script se encarga de:
1.  Cargar los datos iniciales (agenda, usuarios).
2.  Construir y configurar la aplicación del bot con su token.
3.  Programar tareas periódicas (como la comprobación de inactividad).
4.  Registrar todos los manejadores de comandos, callbacks y mensajes.
5.  Iniciar el bot para que comience a recibir actualizaciones.
"""
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
import datetime
from src.config import settings
from src.managers import agenda_manager, user_manager
from src.handlers import general_handlers, agenda_handlers

async def track_activity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Registra la actividad de un usuario en la base de datos.

    Este manejador se ejecuta para cualquier tipo de actualización (`filters.ALL`)
    y llama a `user_manager.update_user_activity` para actualizar la marca
    de tiempo de la última vez que se vio al usuario. No produce una respuesta
    visible para el usuario.

    Args:
        update (Update): El objeto de actualización de Telegram.
        context (ContextTypes.DEFAULT_TYPE): El contexto del bot.
    """
    if update.effective_user:
        user_manager.update_user_activity(update.effective_user)


def main() -> None:
    """Función principal que configura y ejecuta el bot."""
    # Cargar datos al iniciar
    agenda_manager.cargar_agenda()
    user_manager.load_users()

    # Construir la aplicación del bot
    app = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
    
    # Tarea programada para comprobar inactividad
    job_queue = app.job_queue
    job_queue.run_daily(user_manager.check_inactivity_job, time=datetime.time(hour=4, minute=0, second=0))

    # Registrar Handlers
    app.add_handler(CommandHandler("start", general_handlers.start))
    app.add_handler(CommandHandler("agenda", agenda_handlers.agenda_menu))
    app.add_handler(CommandHandler("ia", general_handlers.ask_gemini))
    app.add_handler(CallbackQueryHandler(agenda_handlers.main_agenda_callback_handler))

    # El tracker de actividad se ejecuta para CUALQUIER update
    app.add_handler(MessageHandler(filters.ALL, track_activity_handler), group=1)

    # Handlers específicos que se ejecutan después del tracker
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, agenda_handlers.manejar_mensajes_de_texto), group=2)
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, general_handlers.saludar_nuevo_miembro), group=2)

    # Iniciar el bot
    print("🤖 Bot modular arrancado. ¡A organizar!")
    app.run_polling()

if __name__ == "__main__":
    main()