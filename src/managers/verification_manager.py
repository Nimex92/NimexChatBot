from telegram.ext import ContextTypes
from src.managers import user_manager
from src.config import settings

async def schedule_verification_start(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int):
    """
    Inicia el proceso de verificación para un nuevo usuario.
    Programa la advertencia inicial.
    """
    # Establecer estado inicial
    user_manager.set_user_status(user_id, "pending_presentation")
    
    print(f"⏳ Iniciando verificación para usuario {user_id}. Timeout: {settings.PRESENTATION_TIMEOUT_MINUTES} min.")

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
    Se ejecuta cuando expira el tiempo inicial. Advierte al usuario.
    """
    job = context.job
    user_id = job.data["user_id"]
    chat_id = job.data["chat_id"]
    
    # Verificamos si el usuario ya se ha verificado entre tanto
    current_status = user_manager.get_user_status(user_id)
    if current_status != "pending_presentation":
        return

    # Cambiamos estado a 'warned'
    user_manager.set_user_status(user_id, "warned")
    
    print(f"⚠️ Advertencia de presentación enviada a {user_id}")

    try:
        # Intentamos mencionar al usuario
        # Nota: Para mencionar por ID sin username se usa Markdown: [Nombre](tg://user?id=123)
        # Como no tenemos el nombre a mano en el job, usamos una mención genérica o intentamos recuperarlo.
        # Por simplicidad, un mensaje general citando.
        mention = f"[Nuevo Miembro](tg://user?id={user_id})"
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ ¡Eh, {mention}! Te quedan {settings.PRESENTATION_WARNING_GRACE_MINUTES} minutos para presentarte o tendré que sacarte del grupo. ¡Solo di 'hola' y cuéntanos algo breve!",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"🚨 Error enviando advertencia a {user_id}: {e}")

    # Programar Job de Baneo
    delay_sec = settings.PRESENTATION_WARNING_GRACE_MINUTES * 60
    context.job_queue.run_once(
        ban_job,
        delay_sec,
        chat_id=chat_id,
        user_id=user_id,
        name=f"ban_{user_id}",
        data={"user_id": user_id, "chat_id": chat_id}
    )

async def ban_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Se ejecuta si el usuario ignora la advertencia. Lo expulsa.
    """
    job = context.job
    user_id = job.data["user_id"]
    chat_id = job.data["chat_id"]
    
    current_status = user_manager.get_user_status(user_id)
    if current_status != "warned":
        return

    print(f"👢 Expulsando usuario {user_id} por no presentarse.")

    try:
        # Expulsar (Ban y Unban para que pueda volver más tarde si quiere)
        await context.bot.ban_chat_member(chat_id, user_id)
        await context.bot.unban_chat_member(chat_id, user_id) 
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"👋 Se acabó el tiempo. He expulsado al usuario por no presentarse. ¡Las normas son las normas, majo!"
        )
        
        # Opcional: Limpiar del user_manager si queremos que empiece de 0 si vuelve
        if str(user_id) in user_manager.users_db:
            del user_manager.users_db[str(user_id)]
            user_manager.save_users()
            
    except Exception as e:
        print(f"🚨 Error al expulsar usuario {user_id}: {e}")

def cancel_verification_jobs(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """
    Cancela cualquier tarea pendiente de advertencia o baneo para el usuario.
    """
    print(f"✅ Cancelando jobs de verificación para {user_id}")
    
    jobs_warn = context.job_queue.get_jobs_by_name(f"warn_{user_id}")
    for job in jobs_warn:
        job.schedule_removal()
    
    jobs_ban = context.job_queue.get_jobs_by_name(f"ban_{user_id}")
    for job in jobs_ban:
        job.schedule_removal()
