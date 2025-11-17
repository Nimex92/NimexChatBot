# main.py
import asyncio
import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Importamos desde nuestra nueva estructura en 'src'
from src.config import settings
from src.managers import agenda_manager, user_manager, debate_manager
from src.handlers import general_handlers, agenda_handlers, group_handlers, debate_handlers, level_handlers

async def track_activity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Manejador principal que se ejecuta en cada mensaje.
    Actualiza la actividad del usuario y le otorga XP.
    """
    if not update.effective_user or update.effective_user.is_bot:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id

    # Actualizamos la última vez que se vio al usuario
    user_manager.update_user_activity(user)

    # Otorgamos XP y comprobamos si sube de nivel
    level_up_info = user_manager.grant_xp_on_message(user.id)
    if level_up_info:
        await level_handlers.announce_level_up(context, chat_id, level_up_info)


# --- Funciones del Debate Diario (ahora actúan como wrappers) ---
async def send_daily_debate(context: ContextTypes.DEFAULT_TYPE):
    """Job diario que llama al manager para enviar y anclar el debate."""
    print("⏰ Ejecutando tarea programada: Enviar debate diario.")
    await debate_manager.send_and_pin_debate(context.bot, settings.GROUP_CHAT_ID)

async def unpin_daily_debate(context: ContextTypes.DEFAULT_TYPE):
    """Job diario que llama al manager para desanclar el debate anterior."""
    print("⏰ Ejecutando tarea programada: Desanclar debate anterior.")
    await debate_manager.unpin_previous_debate(context.bot, settings.GROUP_CHAT_ID)


async def main() -> None:
    """
    Función principal que configura y ejecuta el bot de forma asíncrona.
    """
    # Carga de datos
    agenda_manager.cargar_agenda()
    user_manager.load_users()
    debate_manager.load_debate_data()

    app = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()

    # --- Programación de Tareas con APScheduler ---
    scheduler = AsyncIOScheduler(timezone="Europe/Madrid")
    scheduler.add_job(send_daily_debate, CronTrigger(hour=0, minute=0), args=[app])
    scheduler.add_job(unpin_daily_debate, CronTrigger(hour=23, minute=59), args=[app])
    scheduler.start()
    
    job_queue = app.job_queue
    job_queue.run_daily(user_manager.check_inactivity_job, time=datetime.time(hour=4, minute=0, second=0))


    # --- Registrar Handlers ---
    app.add_handler(CommandHandler("start", general_handlers.start))
    app.add_handler(CommandHandler("agenda", agenda_handlers.agenda_menu))
    app.add_handler(CommandHandler("get_group_id", group_handlers.get_group_id_command))
    app.add_handler(CommandHandler("debate", debate_handlers.force_debate_command))
    app.add_handler(CommandHandler("nivel", level_handlers.level_command)) # <-- NUEVO HANDLER
    app.add_handler(CallbackQueryHandler(agenda_handlers.main_agenda_callback_handler))

    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, general_handlers.handle_mention), group=1)
    
    # El manejador de actividad ahora tiene una prioridad más alta para capturar todos los mensajes
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_activity_handler), group=2)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, agenda_handlers.manejar_mensajes_de_texto), group=3)
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, general_handlers.saludar_nuevo_miembro), group=3)

    print("🤖 Bot modular arrancado. Escuchando menciones y con tareas de debate programadas.")
    
    try:
        async with app:
            await app.start()
            await app.updater.start_polling()
            while True:
                await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        print("\n🔌 Deteniendo el bot y el planificador de tareas...")
        scheduler.shutdown()
        print("✅ Planificador detenido.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🔌 Bot detenido.")