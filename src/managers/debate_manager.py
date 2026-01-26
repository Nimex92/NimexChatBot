# src/managers/debate_manager.py
import json
import os
import random
from datetime import datetime
from telegram import Bot
from telegram.ext import ContextTypes
from src.config import settings
from src.managers.ai_manager import generate_text
from src.managers import user_manager

DEBATE_PROMPT = """
Eres un dinamizador de comunidades para un grupo de amigos y ocio en Telegram.
Tu objetivo es generar conversación de forma divertida.

Genera UNA sola pregunta de debate corta, entretenida y ligeramente polémica (pero nunca ofensiva).
Debe ser sobre temas cotidianos, cultura pop o dilemas absurdos.

Ejemplos de inspiración:
- "¿La tortilla, con o sin cebolla?"
- "¿Pizza con piña: genialidad o crimen culinario?"
- "¿Cola Cao o Nesquik?"
- "Si pudieras tener un superpoder inútil, ¿cuál sería?"

Devuelve *únicamente* la pregunta generada, sin saludos ni texto introductorio.
"""

BACKUP_TOPICS = [
    "¿La tortilla de patata: con o sin cebolla?",
    "¿Pizza con piña: sí o no?",
    "¿Eres más de perros o de gatos?",
    "¿Playa o montaña?",
    "¿Qué superpoder elegirías: volar o ser invisible?",
    "¿Nesquik o Cola Cao?",
    "¿Madrugar o trasnochar?",
    "¿Cine en casa o ir al cine?",
    "¿Invierno o verano?",
    "¿Dulce o salado?"
]

debate_data = {}

def load_debate_data():
    """Carga los datos del debate desde el archivo JSON."""
    global debate_data
    try:
        os.makedirs(os.path.dirname(settings.DEBATE_FILE), exist_ok=True)
        with open(settings.DEBATE_FILE, "r", encoding="utf-8") as f:
            debate_data = json.load(f)
        print(f"✅ Datos del debate cargados desde {settings.DEBATE_FILE}")
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"❌ No se encontró {settings.DEBATE_FILE} o está dañado. Se usarán datos vacíos.")
        debate_data = {}

def save_debate_data():
    """Guarda el estado actual de los datos del debate en el archivo JSON."""
    with open(settings.DEBATE_FILE, "w", encoding="utf-8") as f:
        json.dump(debate_data, f, indent=2, ensure_ascii=False)
    print("💾 Datos del debate guardados.")

def load_incitement_templates():
    """Carga las plantillas de mensajes de incitación desde el archivo JSON."""
    try:
        with open(settings.DEBATE_TEMPLATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error cargando plantillas de debate desde {settings.DEBATE_TEMPLATES_FILE}: {e}")
        # Fallback por si falla la carga del archivo
        return [
            "¡Hola {mentions}! ¿Qué opináis de esto: *{topic}*?",
            "¡Aúpa {mentions}! Queremos saber vuestra opinión sobre: *{topic}*",
            "¿Qué nos decís {mentions}? El tema está calentito: *{topic}*"
        ]

async def generate_debate_topic() -> str:
    """Genera una nueva pregunta de debate usando el AIManager, con fallback."""
    print("🧠 Generando nuevo tema de debate...")
    topic = await generate_text(DEBATE_PROMPT)
    
    # Comprobar errores conocidos o respuestas vacías del manager de IA
    if not topic or "¡Ay va!" in topic or "Error" in topic or len(topic) < 5:
        print(f"⚠️ Fallo en la IA o respuesta inválida ('{topic}'). Usando tema de respaldo.")
        topic = random.choice(BACKUP_TOPICS)
    
    # Limpiamos el topic por si la IA devuelve saltos de línea o asteriscos de markdown
    topic = topic.strip().replace('*', '')
    print(f"✨ Tema de debate generado: {topic}")
    return topic

def get_last_debate_message_id() -> int | None:
    """Obtiene el ID del último mensaje de debate anclado."""
    return debate_data.get("last_message_id")

def set_last_debate_info(message_id: int | None, topic: str | None = None):
    """Guarda el ID del mensaje, la fecha actual y el tema."""
    global debate_data
    debate_data["last_message_id"] = message_id
    if message_id:
        debate_data["last_debate_date"] = datetime.now().strftime("%Y-%m-%d")
        if topic:
            debate_data["current_topic"] = topic
    save_debate_data()

async def send_and_pin_debate(bot: Bot, chat_id: int):
    """
    Orquesta la generación, envío y anclaje de un nuevo debate.
    """
    print("🚀 Iniciando ciclo de envío de debate...")
    try:
        topic = await generate_debate_topic()
        message = await bot.send_message(
            chat_id=chat_id,
            text=f"🤔 DEBATE DEL DÍA 🤔\n\n{topic}"
        )
        await bot.pin_chat_message(
            chat_id=chat_id,
            message_id=message.message_id
        )
        set_last_debate_info(message.message_id, topic)
        print(f"✅ Debate enviado y anclado. ID: {message.message_id}")
        return f"¡Nuevo debate iniciado!\n\n{topic}"
    except Exception as e:
        print(f"🚨 Error al enviar y anclar el debate: {e}")
        return "❌ Uups! Hubo un error al intentar iniciar el debate."

async def unpin_previous_debate(bot: Bot, chat_id: int):
    """Desancla el debate del día anterior."""
    print("🧹 Limpiando debate anterior...")
    last_message_id = get_last_debate_message_id()
    if last_message_id:
        try:
            await bot.unpin_chat_message(
                chat_id=chat_id,
                message_id=last_message_id
            )
            set_last_debate_info(None) # Limpiamos ID
            print(f"✅ Debate desanclado. ID: {last_message_id}")
        except Exception as e:
            print(f"ℹ️ No se pudo desanclar el debate. Quizás fue borrado. ID: {last_message_id}. Error: {e}")
    else:
        print("ℹ️ No había debate anterior para desanclar.")

async def check_and_run_startup_debate(bot: Bot, chat_id: int):
    """
    Comprueba si ya hay un debate para el día de hoy. Si no, lo genera.
    Se ejecuta al iniciar el bot.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    last_date = debate_data.get("last_debate_date")
    
    print(f"🔎 Comprobando debate de arranque. Hoy: {today_str}, Último: {last_date}")
    
    if last_date != today_str:
        print("⚠️ No hay debate registrado para hoy. Generando uno ahora...")
        # Desanclar el anterior por si acaso quedó colgado
        await unpin_previous_debate(bot, chat_id)
        # Generar uno nuevo
        await send_and_pin_debate(bot, chat_id)
    else:
        print("✅ Ya existe un debate generado para hoy. No se requiere acción.")

# --- Funciones de Incitación a la Participación ---

def schedule_next_incitement(job_queue):
    """Programa la siguiente incitación al debate en un intervalo aleatorio (1-3h)."""
    # 1 a 3 horas en segundos = 3600 a 10800
    delay = random.randint(3600, 10800)
    print(f"🎲 Próxima incitación al debate programada en {delay/60:.1f} minutos.")
    job_queue.run_once(incite_participation_job, delay)

async def incite_participation_job(context: ContextTypes.DEFAULT_TYPE):
    """Job que se ejecuta para incitar a la participación."""
    chat_id = settings.GROUP_CHAT_ID
    
    # 1. Verificar si hay un debate activo hoy y tenemos el tema
    today_str = datetime.now().strftime("%Y-%m-%d")
    last_date = debate_data.get("last_debate_date")
    topic = debate_data.get("current_topic")
    
    if last_date != today_str or not topic:
        print("ℹ️ No se incita al debate porque no hay uno activo (o falta el tema) para hoy.")
        schedule_next_incitement(context.job_queue)
        return

    # 2. Seleccionar usuarios aleatorios (3)
    users = user_manager.get_random_verified_users(3)
    if not users:
        print("ℹ️ No hay usuarios verificados suficientes para mencionar.")
        schedule_next_incitement(context.job_queue)
        return

    # 3. Construir mensaje
    mentions = []
    for u in users:
        # Intentamos mencionar con Markdown [Nombre](tg://user?id=123)
        mentions.append(f"[{u['name']}](tg://user?id={u['id']})")
    
    mentions_str = ", ".join(mentions)
    
    # Cargamos las plantillas desde el archivo JSON
    mensajes_incitacion = load_incitement_templates()
    
    # Elegimos una plantilla y rellenamos los huecos
    template = random.choice(mensajes_incitacion)
    text = template.format(mentions=mentions_str, topic=topic)

    try:
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        print("📢 Incitación al debate enviada.")
    except Exception as e:
        print(f"🚨 Error enviando incitación: {e}")

    # 4. Programar la siguiente
    schedule_next_incitement(context.job_queue)
