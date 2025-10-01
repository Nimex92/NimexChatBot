# src/managers/user_manager.py
"""Módulo para gestionar la base de datos de usuarios y su actividad."""
import json
import os
from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from telegram import User

from src.config import settings

users_db = {}

def load_users():
    """Carga la base de datos de usuarios desde un archivo JSON.

    Intenta leer el archivo definido en `settings.USERS_FILE`. Si el archivo
    no se encuentra o contiene JSON inválido, inicializa una base de datos
    vacía en memoria y muestra un mensaje informativo.
    """
    global users_db
    try:
        with open(settings.USERS_FILE, "r", encoding="utf-8") as f:
            users_db = json.load(f)
        print(f"✅ Base de datos de usuarios cargada desde {settings.USERS_FILE}")
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"❌ No se encontró {settings.USERS_FILE}. Se creará una nueva.")
        users_db = {}

def save_users():
    """Guarda el estado actual de la base de datos de usuarios en un archivo JSON.

    Serializa el diccionario `users_db` a JSON y lo escribe en el archivo
    definido en `settings.USERS_FILE`, asegurando la persistencia de los datos.
    """
    with open(settings.USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_db, f, indent=2, ensure_ascii=False)
    print("💾 Base de datos de usuarios guardada.")

def update_user_activity(user: User):
    """Registra o actualiza la última actividad de un usuario.

    Si el usuario no existe en la base de datos, lo crea con datos básicos
    como su nombre, fecha de registro y un número inicial de "vidas".
    Para usuarios existentes, simplemente actualiza la marca de tiempo de su
    última actividad (`last_seen`).

    Args:
        user (telegram.User): El objeto de usuario de `python-telegram-bot`
            que contiene los datos del usuario que ha interactuado.
    """
    user_id = str(user.id) # Las claves en JSON deben ser strings
    last_seen_iso = datetime.now().isoformat()

    if user_id not in users_db:
        users_db[user_id] = {
            "first_name": user.first_name,
            "username": user.username,
            "join_date": last_seen_iso,
            "lives": 3,
        }
    
    users_db[user_id]["last_seen"] = last_seen_iso
    save_users()

async def check_inactivity_job(context: ContextTypes.DEFAULT_TYPE):
    """Comprueba la inactividad de los usuarios y gestiona el sistema de vidas.

    Esta función está diseñada para ser ejecutada como un trabajo programado
    diario. Itera sobre todos los usuarios registrados y comprueba si su última
    actividad supera el umbral de inactividad definido.

    Si un usuario está inactivo:
    1.  Se le resta una "vida".
    2.  Se le notifica por mensaje privado (si es posible).
    3.  Se resetea su contador de inactividad para el siguiente ciclo.

    Si las vidas de un usuario llegan a cero, es expulsado del grupo y eliminado
    de la base de datos.

    Args:
        context (ContextTypes.DEFAULT_TYPE): El contexto del bot de `python-telegram-bot`,
            usado para acceder al bot y enviar mensajes o realizar acciones de chat.
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