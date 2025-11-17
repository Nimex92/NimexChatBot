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
from src.handlers import general_handlers, agenda_handlers, group_handlers

async def track_activity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user:
        user_manager.update_user_activity(update.effective_user)

# --- Funciones del Debate Diario ---
async def send_daily_debate(context: ContextTypes.DEFAULT_TYPE):
    """Genera, envía y ancla el debate del día."""
    print("⏰ Ejecutando tarea: Enviar debate diario.")
    try:
        topic = await debate_manager.generate_debate_topic()
        message = await context.bot.send_message(
            chat_id=settings.GROUP_CHAT_ID,
            text=f"🤔 DEBATE DEL DÍA 🤔\n\n{topic}"
        )
        await context.bot.pin_chat_message(
            chat_id=settings.GROUP_CHAT_ID,
            message_id=message.message_id
        )
        debate_manager.set_last_debate_message_id(message.message_id)
        print(f"✅ Debate enviado y anclado. ID: {message.message_id}")
    except Exception as e:
        print(f"🚨 Error al enviar el debate diario: {e}")

async def unpin_daily_debate(context: ContextTypes.DEFAULT_TYPE):
    """Desancla el debate del día anterior."""
    print("⏰ Ejecutando tarea: Desanclar debate anterior.")
    last_message_id = debate_manager.get_last_debate_message_id()
    if last_message_id:
        try:
            await context.bot.unpin_chat_message(
                chat_id=settings.GROUP_CHAT_ID,
                message_id=last_message_id
            )
            debate_manager.set_last_debate_message_id(None)
            print(f"✅ Debate desanclado. ID: {last_message_id}")
        except Exception as e:
            # Es común que el mensaje ya no exista o no se pueda desanclar, lo logeamos como info
            print(f"ℹ️ No se pudo desanclar el debate. Quizás fue borrado. ID: {last_message_id}. Error: {e}")
    else:
        print("ℹ️ No había debate anterior para desanclar.")


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
    # Pasamos el 'app' como contexto a las tareas para que puedan usar el bot
    scheduler = AsyncIOScheduler(timezone="Europe/Madrid")
    scheduler.add_job(send_daily_debate, CronTrigger(hour=0, minute=0), args=[app])
    scheduler.add_job(unpin_daily_debate, CronTrigger(hour=23, minute=59), args=[app])
    scheduler.start()
    
    # Tarea de inactividad (usando el job_queue del bot, que es más simple para tareas diarias)
    job_queue = app.job_queue
    job_queue.run_daily(user_manager.check_inactivity_job, time=datetime.time(hour=4, minute=0, second=0))


    # --- Registrar Handlers ---
    app.add_handler(CommandHandler("start", general_handlers.start))
    app.add_handler(CommandHandler("agenda", agenda_handlers.agenda_menu))
    app.add_handler(CommandHandler("get_group_id", group_handlers.get_group_id_command))
    app.add_handler(CallbackQueryHandler(agenda_handlers.main_agenda_callback_handler))

    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, general_handlers.handle_mention), group=1)
    
    app.add_handler(MessageHandler(filters.ALL, track_activity_handler), group=2)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, agenda_handlers.manejar_mensajes_de_texto), group=3)
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, general_handlers.saludar_nuevo_miembro), group=3)

    print("🤖 Bot modular arrancado. Escuchando menciones y con tareas de debate programadas.")
    
    try:
        async with app:
            await app.start()
            await app.updater.start_polling()
            # Bucle para mantener el script principal vivo y permitir que APScheduler trabaje en segundo plano
            while True:
                await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        print("\n🔌 Deteniendo el bot y el planificador de tareas...")
        scheduler.shutdown()
        print("✅ Planificador detenido.")
        # La salida del `async with app` se encargará de detener el bot de forma limpia.


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🔌 Bot detenido.")