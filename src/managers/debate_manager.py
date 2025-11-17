# src/managers/debate_manager.py
import json
import os
from telegram import Bot
from src.config import settings
from src.managers.ai_manager import generate_text

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

async def generate_debate_topic() -> str:
    """Genera una nueva pregunta de debate usando el AIManager."""
    print("🧠 Generando nuevo tema de debate...")
    topic = await generate_text(DEBATE_PROMPT)
    # Limpiamos el topic por si la IA devuelve saltos de línea o asteriscos de markdown
    topic = topic.strip().replace('*', '')
    print(f"✨ Tema de debate generado: {topic}")
    return topic

def get_last_debate_message_id() -> int | None:
    """Obtiene el ID del último mensaje de debate anclado."""
    return debate_data.get("last_message_id")

def set_last_debate_message_id(message_id: int | None):
    """Guarda el ID del último mensaje de debate anclado."""
    global debate_data
    debate_data["last_message_id"] = message_id
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
        set_last_debate_message_id(message.message_id)
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
            set_last_debate_message_id(None)
            print(f"✅ Debate desanclado. ID: {last_message_id}")
        except Exception as e:
            print(f"ℹ️ No se pudo desanclar el debate. Quizás fue borrado. ID: {last_message_id}. Error: {e}")
    else:
        print("ℹ️ No había debate anterior para desanclar.")
