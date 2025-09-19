# src/managers/user_manager.py
import json
import os
from datetime import datetime, timedelta
from telegram.ext import ContextTypes

from src.config import settings

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
        json.dump(users_db, f, indent=2)
    print("💾 Base de datos de usuarios guardada.")

def update_user_activity(user):
    """
    Registra o actualiza la última actividad de un usuario.
    """
    user_id = str(user.id) # Las claves en JSON deben ser strings
    
    # Usamos la fecha actual en formato ISO 8601
    last_seen_iso = datetime.now().isoformat()

    if user_id not in users_db:
        # Si es un usuario nuevo, guardamos más datos
        users_db[user_id] = {
            "first_name": user.first_name,
            "username": user.username,
            "join_date": last_seen_iso,
            "lives": 3,  # Vidas iniciales
        }
    
    # Siempre actualizamos la última vez que se le vio activo
    users_db[user_id]["last_seen"] = last_seen_iso
    save_users()

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
    
    # Iteramos sobre una copia de las claves para poder modificar el diccionario
    for user_id in list(users_db.keys()):
        data = users_db[user_id]
        
        # Usamos .get() para dar 3 vidas por defecto a usuarios antiguos que no tengan el campo
        lives = data.get("lives", 3)
        last_seen = datetime.fromisoformat(data["last_seen"])

        # Comprobamos si ha pasado el tiempo de inactividad
        if (now - last_seen) > threshold:
            lives -= 1
            print(f"💔 Usuario {user_id} ha perdido una vida por inactividad. Vidas restantes: {lives}")
            
            # Actualizamos sus datos en la BBDD
            data["lives"] = lives
            # ¡Importante! Reseteamos su contador de inactividad
            data["last_seen"] = now.isoformat() 

            # Opcional: Notificar al usuario por privado que ha perdido una vida
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

    # Ahora expulsamos a todos los que se quedaron sin vidas
    if users_to_kick:
        print(f"👢 Expulsando a {len(users_to_kick)} usuarios...")
        for user_id in users_to_kick:
            try:
                await context.bot.kick_chat_member(chat_id=chat_id, user_id=int(user_id))
                await context.bot.unban_chat_member(chat_id=chat_id, user_id=int(user_id))
                print(f"✅ Usuario {user_id} expulsado.")
                # Lo eliminamos de nuestra base de datos
                del users_db[user_id]
            except Exception as e:
                print(f"🚨 Error al expulsar al usuario {user_id}: {e}")
    else:
        print("👍 Ningún usuario ha llegado a cero vidas hoy.")

    save_users() # Guardamos todos los cambios al final
    """
    La función que se ejecutará diariamente para buscar y expulsar inactivos.
    """
    print(f"🏃 Ejecutando tarea diaria de comprobación de inactividad...")
    
    chat_id = settings.GROUP_CHAT_ID
    if not chat_id:
        print("❌ No se ha configurado un GROUP_CHAT_ID. La tarea no se ejecutará.")
        return

    inactive_user_ids = get_inactive_users()
    
    if not inactive_user_ids:
        print("👍 No se encontraron usuarios inactivos.")
        return

    print(f"👻 Encontrados {len(inactive_user_ids)} usuarios inactivos para expulsar.")
    
    for user_id in inactive_user_ids:
        try:
            # Expulsamos al usuario
            await context.bot.kick_chat_member(chat_id=chat_id, user_id=int(user_id))
            
            # ¡Importante! Lo "des-baneamos" inmediatamente para que pueda volver a unirse si quiere
            await context.bot.unban_chat_member(chat_id=chat_id, user_id=int(user_id))
            
            print(f"👢 Usuario {user_id} expulsado por inactividad.")
            
            # Opcional: eliminarlo de nuestra BBDD
            del users_db[str(user_id)]

        except Exception as e:
            print(f"🚨 Error al expulsar al usuario {user_id}: {e}")
    
    save_users() # Guardamos los cambios en la BBDD