# src/managers/user_manager.py
import json
import os
import random
from datetime import datetime, timedelta
from time import time
from telegram.ext import ContextTypes

from src.config import settings, levels

users_db = {}

def load_users():
    """Carga la base de datos de usuarios desde el archivo JSON."""
    global users_db
    try:
        with open(settings.USERS_FILE, "r", encoding="utf-8") as f:
            users_db = json.load(f)
        print(f"✅ Base de datos de usuarios cargada desde {settings.USERS_FILE}")
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"❌ No se encontró {settings.USERS_FILE}. Se creará una nueva.")
        users_db = {}

def save_users():
    """Guarda la base de datos de usuarios en el archivo JSON."""
    with open(settings.USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_db, f, indent=2, ensure_ascii=False)
    print("💾 Base de datos de usuarios guardada.")

def update_user_activity(user):
    """
    Registra o actualiza la última actividad de un usuario y sus datos de nivel.
    """
    user_id = str(user.id)
    now_iso = datetime.now().isoformat()

    if user_id not in users_db:
        users_db[user_id] = {
            "first_name": user.first_name,
            "username": user.username,
            "join_date": now_iso,
            "lives": 3,
            "level": 1,
            "xp": 0,
            "last_xp_timestamp": 0,
            "status": "pending_presentation" # Por defecto, nuevos usuarios deben presentarse
        }
    
    user_data = users_db[user_id]
    user_data["last_seen"] = now_iso
    
    # Asegurar compatibilidad con usuarios antiguos
    if "level" not in user_data:
        user_data["level"] = 1
        user_data["xp"] = 0
        user_data["last_xp_timestamp"] = 0

    save_users()

def grant_xp_on_message(user_id: int) -> dict | None:
    """
    Otorga XP a un usuario por enviar un mensaje si ha pasado el cooldown.
    Devuelve los detalles del nuevo nivel si el usuario sube de nivel.
    """
    user_id_str = str(user_id)
    if user_id_str not in users_db:
        return None

    user_data = users_db[user_id_str]
    
    # 1. Comprobar Cooldown
    if time() - user_data.get("last_xp_timestamp", 0) > levels.XP_COOLDOWN_SECONDS:
        # 2. Otorgar XP
        user_data["xp"] += levels.XP_PER_MESSAGE
        user_data["last_xp_timestamp"] = time()
        print(f"✨ Usuario {user_id_str} ha ganado {levels.XP_PER_MESSAGE} XP. Total: {user_data['xp']}")

        # 3. Comprobar si sube de nivel
        current_level = user_data.get("level", 1)
        next_level_xp = levels.get_next_level_xp(current_level)

        if next_level_xp is not None and user_data["xp"] >= next_level_xp:
            new_level, new_level_name = levels.get_level_for_xp(user_data["xp"])
            
            if new_level > current_level:
                user_data["level"] = new_level
                save_users()
                print(f"🎉 ¡LEVEL UP! Usuario {user_id_str} ha subido al nivel {new_level}: {new_level_name}")
                return {
                    "user_name": user_data["first_name"],
                    "level_num": new_level,
                    "level_name": new_level_name
                }
        
        save_users()
    
    return None

def get_user_level_info(user_id: int) -> dict | None:
    """
    Devuelve la información de nivel y progreso de un usuario.
    """
    user_id_str = str(user_id)
    if user_id_str not in users_db:
        return None
        
    user_data = users_db[user_id_str]
    current_level = user_data.get("level", 1)
    current_xp = user_data.get("xp", 0)
    
    level_name = levels.LEVEL_THRESHOLDS.get(current_level, {}).get("name", "Nivel Desconocido")
    
    xp_for_current_level = levels.calculate_xp_for_level(current_level)
    xp_for_next_level = levels.get_next_level_xp(current_level)

    return {
        "name": user_data["first_name"],
        "level": current_level,
        "level_name": level_name,
        "xp": current_xp,
        "xp_base_level": xp_for_current_level,
        "xp_next_level": xp_for_next_level
    }

def get_random_verified_users(count: int = 3) -> list[dict]:
    """
    Devuelve una lista aleatoria de usuarios verificados.
    Cada elemento es un dict con 'id' y 'name' (o username).
    """
    verified_users = []
    for uid, data in users_db.items():
        if data.get("status") == "verified":
            # Preferimos first_name, si no username, si no "Usuario"
            name = data.get("first_name") or data.get("username") or "Usuario"
            verified_users.append({"id": uid, "name": name})
    
    if not verified_users:
        return []
    
    # Seleccionamos aleatoriamente hasta 'count' usuarios
    sample_size = min(len(verified_users), count)
    return random.sample(verified_users, sample_size)

# --- Funciones de Estado (Verificación) ---

def set_user_status(user_id: int, status: str):
    """
    Establece el estado de verificación de un usuario.
    Estados: 'verified', 'pending_presentation', 'warned'
    """
    user_id_str = str(user_id)
    if user_id_str in users_db:
        users_db[user_id_str]["status"] = status
        save_users()

def get_user_status(user_id: int) -> str:
    """
    Obtiene el estado de verificación de un usuario.
    Por defecto, si no tiene estado, se asume 'verified' (para usuarios antiguos).
    """
    user_id_str = str(user_id)
    if user_id_str in users_db:
        return users_db[user_id_str].get("status", "verified")
    return "verified"

def is_verified(user_id: int) -> bool:
    """Devuelve True si el usuario está verificado."""
    return get_user_status(user_id) == "verified"


async def check_inactivity_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Se ejecuta diariamente. Comprueba la inactividad, resta vidas y expulsa si llegan a cero.
    """
    print(f"🏃 Ejecutando tarea diaria de comprobación de vidas por inactividad...")
    
    chat_id = settings.GROUP_CHAT_ID
    if not chat_id:
        print("❌ No se ha configurado un GROUP_CHAT_ID. La tarea no se ejecutará.")
        return

    now = datetime.now()
    threshold = timedelta(days=settings.INACTIVITY_DAYS)
    users_to_kick = []
    
    for user_id in list(users_db.keys()):
        data = users_db[user_id]
        
        lives = data.get("lives", 3)
        last_seen = datetime.fromisoformat(data["last_seen"])

        if (now - last_seen) > threshold:
            lives -= 1
            print(f"💔 Usuario {user_id} ha perdido una vida por inactividad. Vidas restantes: {lives}")
            
            data["lives"] = lives
            data["last_seen"] = now.isoformat() 

            try:
                await context.bot.send_message(
                    chat_id=int(user_id),
                    text=f"Hola 👋, solo para que lo sepas, has perdido una vida en el grupo por inactividad. Te quedan {lives}."
                         "\n¡Participa en el chat o apúntate a un evento para mantenerte activo!"
                )
            except Exception:
                print(f"No se pudo notificar al usuario {user_id} (probablemente ha bloqueado al bot).")

            if lives <= 0:
                print(f"☠️ Usuario {user_id} se ha quedado sin vidas. Programado para expulsión.")
                users_to_kick.append(user_id)

    if users_to_kick:
        print(f"👢 Expulsando a {len(users_to_kick)} usuarios...")
        for user_id in users_to_kick:
            try:
                await context.bot.kick_chat_member(chat_id=chat_id, user_id=int(user_id))
                await context.bot.unban_chat_member(chat_id=chat_id, user_id=int(user_id))
                print(f"✅ Usuario {user_id} expulsado.")
                del users_db[user_id]
            except Exception as e:
                print(f"🚨 Error al expulsar al usuario {user_id}: {e}")
    else:
        print("👍 Ningún usuario ha llegado a cero vidas hoy.")

    save_users()