# src/config/settings.py
import os
from dotenv import load_dotenv
import google.generativeai as genai # <-- AÑADIR

load_dotenv()

# --- Claves y Tokens ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Rutas ---
AGENDA_FILE = "data/agenda.json"
USERS_FILE = "data/users.json"
DEBATE_FILE = "data/debate.json"
DEBATE_TEMPLATES_FILE = "data/welcome_debate_message.json"
WORD_GAME_FILE = "data/word_game.json"

# --- Configuración del Módulo de Usuarios ---
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", 0))
INACTIVITY_DAYS = int(os.getenv("INACTIVITY_DAYS", 30))
PRESENTATION_TIMEOUT_MINUTES = int(os.getenv("PRESENTATION_TIMEOUT_MINUTES", 10))
PRESENTATION_WARNING_GRACE_MINUTES = int(os.getenv("PRESENTATION_WARNING_GRACE_MINUTES", 5))

# --- Configuración del Juego de la Palabra ---
WORD_GAME_POINTS = int(os.getenv("WORD_GAME_POINTS", 50))

# --- Clientes de Servicios ---
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
