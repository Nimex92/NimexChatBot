# src/config/settings.py
import os
from dotenv import load_dotenv
import google.generativeai as genai # <-- AÑADIR

load_dotenv()

# --- Claves y Tokens ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # <-- AÑADIR

# --- Rutas ---
AGENDA_FILE = "data/agenda.json"
USERS_FILE = "data/users.json"
DEBATE_FILE = "data/debate.json"

# --- Configuración del Módulo de Usuarios ---
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", 0))
INACTIVITY_DAYS = int(os.getenv("INACTIVITY_DAYS", 30))

# --- Clientes de Servicios ---
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY) # <-- AÑADIR