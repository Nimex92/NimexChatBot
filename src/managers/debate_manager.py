# src/managers/debate_manager.py
import json
import os
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
