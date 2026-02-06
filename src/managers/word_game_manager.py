# src/managers/word_game_manager.py
import json
import os
import random
import html
import re
from datetime import datetime
from telegram.ext import ContextTypes

from src.config import settings

game_data = {}

WORDS = [
    "rioja",
    "vino",
    "amigo",
    "fiesta",
    "pintxo",
    "botella",
    "musica",
    "cuadrilla",
    "tardeo",
    "verano",
    "invierno",
    "montana",
    "playa",
    "chuleton",
    "torneo",
    "cafe",
    "helado",
    "parque",
    "futbol",
    "pelota"
]

def load_word_game_data():
    """Carga el estado del juego desde el archivo JSON."""
    global game_data
    try:
        os.makedirs(os.path.dirname(settings.WORD_GAME_FILE), exist_ok=True)
        with open(settings.WORD_GAME_FILE, "r", encoding="utf-8") as f:
            game_data = json.load(f)
        print(f"✅ Datos del juego de palabra cargados desde {settings.WORD_GAME_FILE}")
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"❌ No se encontró {settings.WORD_GAME_FILE} o está dañado. Se usarán datos vacíos.")
        game_data = {}

def save_word_game_data():
    """Guarda el estado del juego en el archivo JSON."""
    os.makedirs(os.path.dirname(settings.WORD_GAME_FILE), exist_ok=True)
    with open(settings.WORD_GAME_FILE, "w", encoding="utf-8") as f:
        json.dump(game_data, f, indent=2, ensure_ascii=False)
    print("💾 Datos del juego de palabra guardados.")

def is_game_active() -> bool:
    return bool(game_data.get("active"))

def get_current_word() -> str | None:
    return game_data.get("current_word")

def set_game_state(active: bool, word: str | None = None, message_id: int | None = None):
    game_data["active"] = active
    game_data["current_word"] = word if active else None
    game_data["last_message_id"] = message_id
    game_data["last_started_at"] = datetime.now().isoformat() if active else None
    save_word_game_data()

def normalize_guess(text: str) -> str:
    if not text:
        return ""
    text = text.strip().lower()
    return re.sub(r"[^a-z0-9ñáéíóúü]", "", text)

def is_correct_guess(text: str) -> bool:
    if not is_game_active():
        return False
    word = get_current_word()
    if not word:
        return False
    return normalize_guess(text) == normalize_guess(word)

async def start_new_round(context: ContextTypes.DEFAULT_TYPE):
    chat_id = settings.GROUP_CHAT_ID
    if not chat_id:
        print("❌ No se ha configurado GROUP_CHAT_ID. El juego no se iniciará.")
        return

    if is_game_active():
        print("ℹ️ Ya hay un juego activo. No se inicia una nueva ronda.")
        return

    word = random.choice(WORDS)
    spoiler_word = f"<span class=\"tg-spoiler\">{html.escape(word)}</span>"
    text = (
        "Juego de la palabra\n"
        f"Adivina: {spoiler_word}\n"
        f"El primero que la escriba gana {settings.WORD_GAME_POINTS} puntos"
    )

    try:
        message = await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        set_game_state(True, word, message.message_id)
        print(f"✅ Nueva ronda iniciada. Palabra: {word}")
    except Exception as e:
        print(f"🚨 Error enviando la palabra del juego: {e}")

def finish_round():
    if not is_game_active():
        return
    set_game_state(False)

def schedule_next_word_game(job_queue):
    """Programa la siguiente ronda en un intervalo aleatorio (1-3h)."""
    delay = random.randint(3600, 10800)
    print(f"🎲 Próxima ronda del juego programada en {delay/60:.1f} minutos.")
    job_queue.run_once(word_game_job, delay)

async def word_game_job(context: ContextTypes.DEFAULT_TYPE):
    await start_new_round(context)
    schedule_next_word_game(context.job_queue)
