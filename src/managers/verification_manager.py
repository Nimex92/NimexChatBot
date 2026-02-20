from telegram.ext import ContextTypes
from src.managers import user_manager
from src.config import settings

async def schedule_verification_start(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int):
    """
    Inicia el proceso de verificación para un nuevo usuario.
    Programa la advertencia inicial.
    """
    # Establecer estado inicial
    user_manager.set_user_status(user_id, "pending_rules")
    
    print(f"⏳ Iniciando verificación de normas para usuario {user_id}. Timeout: {settings.PRESENTATION_TIMEOUT_MINUTES} min.")

    # Programar Job de Advertencia
    delay_sec = settings.PRESENTATION_TIMEOUT_MINUTES * 60
    context.job_queue.run_once(
        warning_job, 
        delay_sec, 
        chat_id=chat_id, 
        user_id=user_id,
        name=f"warn_{user_id}",
        data={"user_id": user_id, "chat_id": chat_id}
    )

async def warning_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Se ejecuta cuando expira el tiempo inicial. Recuerda aceptar normas.
    """
    job = context.job
    user_id = job.data["user_id"]
    chat_id = job.data["chat_id"]
    
    # Verificamos si el usuario ya se ha verificado entre tanto
    current_status = user_manager.get_user_status(user_id)
    if current_status != "pending_rules":
        return

    print(f"⚠️ Recordatorio de aceptación de normas enviado a {user_id}")

    try:
        # Intentamos mencionar al usuario
        # Nota: Para mencionar por ID sin username se usa Markdown: [Nombre](tg://user?id=123)
        # Como no tenemos el nombre a mano en el job, usamos una mención genérica o intentamos recuperarlo.
        # Por simplicidad, un mensaje general citando.
        mention = f"[Nuevo Miembro](tg://user?id={user_id})"
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"⚠️ ¡Eh, {mention}! Para desbloquear el bot solo tienes que aceptar las normas.\n"
                "Escribe algo como: *acepto las normas*."
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"🚨 Error enviando advertencia a {user_id}: {e}")

def cancel_verification_jobs(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """
    Cancela cualquier tarea pendiente de recordatorio para el usuario.
    """
    print(f"✅ Cancelando jobs de verificación para {user_id}")
    
    jobs_warn = context.job_queue.get_jobs_by_name(f"warn_{user_id}")
    for job in jobs_warn:
        job.schedule_removal()
