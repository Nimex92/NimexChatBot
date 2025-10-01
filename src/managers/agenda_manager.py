# src/managers/agenda_manager.py
"""Módulo de gestión de la agenda de eventos.

Este módulo es el único responsable de interactuar con la estructura de datos
de la agenda. Contiene funciones para cargar, guardar, crear, modificar y
consultar eventos. La agenda se mantiene en memoria en un `defaultdict` y
se persiste en un archivo JSON.
"""
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta
from babel.dates import format_datetime
import locale

from src.config import settings
from src.managers import user_manager

locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

agenda = defaultdict(list)

def cargar_agenda():
    """Carga la agenda desde el archivo JSON al iniciar el bot.

    Intenta leer y parsear el archivo definido en `settings.AGENDA_FILE`.
    Si el archivo no existe o está corrupto, inicializa una agenda vacía.
    """
    global agenda
    try:
        os.makedirs(os.path.dirname(settings.AGENDA_FILE), exist_ok=True)
        with open(settings.AGENDA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Reconstruimos el defaultdict desde el dict cargado
            agenda = defaultdict(list, {k: v for k, v in data.items()})
        print(f"✅ Agenda cargada desde {settings.AGENDA_FILE}")
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"❌ No se encontró {settings.AGENDA_FILE} o está dañado. Se usará una agenda vacía.")
        agenda = defaultdict(list)

def guardar_agenda():
    """Guarda el estado actual de la agenda en el archivo JSON."""
    with open(settings.AGENDA_FILE, "w", encoding="utf-8") as f:
        json.dump(agenda, f, indent=2, ensure_ascii=False)
    print("💾 Agenda guardada.")

def crear_evento(fecha: str, hora: str, titulo: str, creador_id: int):
    """Añade un nuevo evento a la agenda y persiste los cambios.

    Args:
        fecha (str): La fecha del evento en formato 'YYYY-MM-DD'.
        hora (str): La hora del evento en formato 'HH:MM'.
        titulo (str): El nombre o descripción del evento.
        creador_id (int): El ID de Telegram del usuario que crea el evento.
    """
    evento = {
        "hora": hora,
        "titulo": titulo,
        "asistentes": [],
        "creador_id": creador_id,
        "activo": True
    }
    agenda[fecha].append(evento)
    guardar_agenda()

def desactivar_evento(fecha: str, idx: int) -> dict | None:
    """Marca un evento como inactivo (borrado lógico).

    Args:
        fecha (str): La fecha del evento a desactivar.
        idx (int): El índice del evento en la lista de esa fecha.

    Returns:
        dict | None: El diccionario del evento desactivado o None si no se encontró.
    """
    if fecha in agenda and len(agenda[fecha]) > idx:
        agenda[fecha][idx]['activo'] = False
        guardar_agenda()
        return agenda[fecha][idx]
    return None

def inscribir_usuario(fecha: str, idx: int, user_info: dict) -> bool:
    """Inscribe un usuario a un evento, evitando duplicados.

    Además de añadir al usuario a la lista de asistentes, también actualiza
    la última actividad del usuario a través de `user_manager`.

    Args:
        fecha (str): La fecha del evento.
        idx (int): El índice del evento en la lista de esa fecha.
        user_info (dict): Un diccionario con 'id', 'nombre' y 'username' del usuario.

    Returns:
        bool: True si el usuario fue inscrito, False si ya estaba inscrito.
    """
    evento = agenda[fecha][idx]
    if not any(a.get("id") == user_info["id"] for a in evento["asistentes"]):
        evento["asistentes"].append(user_info)
        guardar_agenda()

        from types import SimpleNamespace
        user_obj = SimpleNamespace(**user_info)
        user_manager.update_user_activity(user_obj)
        return True
    return False

def desinscribir_usuario(fecha: str, idx: int, user_id: int) -> bool:
    """Da de baja a un usuario de un evento.

    Args:
        fecha (str): La fecha del evento.
        idx (int): El índice del evento en la lista de esa fecha.
        user_id (int): El ID del usuario a dar de baja.

    Returns:
        bool: True si el usuario fue eliminado, False si no se encontró.
    """
    evento = agenda[fecha][idx]
    asistentes_antes = len(evento["asistentes"])
    evento["asistentes"] = [a for a in evento["asistentes"] if a.get("id") != user_id]
    if len(evento["asistentes"]) < asistentes_antes:
        guardar_agenda()
        return True
    return False

def obtener_eventos_activos(fecha_inicio: str = None, fecha_fin: str = None) -> list:
    """Devuelve una lista de eventos activos para un rango de fechas.

    Si no se proporcionan fechas, por defecto busca en los próximos 14 días.

    Args:
        fecha_inicio (str, optional): Fecha de inicio en formato 'YYYY-MM-DD'.
        fecha_fin (str, optional): Fecha de fin en formato 'YYYY-MM-DD'.

    Returns:
        list: Una lista de diccionarios, donde cada uno contiene la fecha
              y la lista de eventos para esa fecha.
    """
    eventos_por_fecha = []
    hoy = datetime.today().date()

    if fecha_inicio and fecha_fin:
        start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        fechas = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    else:
        fechas = [hoy + timedelta(days=i) for i in range(14)]

    for fecha in fechas:
        clave_fecha = fecha.strftime("%Y-%m-%d")
        if clave_fecha in agenda:
            eventos_activos = [
                (idx, evento) for idx, evento in enumerate(agenda[clave_fecha])
                if evento.get('activo', True)
            ]
            if eventos_activos:
                eventos_por_fecha.append({'fecha': clave_fecha, 'eventos': eventos_activos})
    return eventos_por_fecha

def obtener_eventos_inscrito(user_id: int, dias: int = 30) -> list:
    """Busca los eventos futuros en los que un usuario está inscrito.

    Args:
        user_id (int): El ID de Telegram del usuario.
        dias (int, optional): El número de días hacia el futuro a buscar. Por defecto 30.

    Returns:
        list: Una lista de diccionarios, cada uno representando un evento en
              el que el usuario está inscrito. Incluye fecha, índice y datos del evento.
    """
    eventos_inscrito = []
    hoy = datetime.today()
    for i in range(dias):
        fecha = hoy + timedelta(days=i)
        clave_fecha = fecha.strftime("%Y-%m-%d")
        if clave_fecha in agenda:
            for idx, evento in enumerate(agenda[clave_fecha]):
                if evento.get('activo', True) and any(a.get("id") == user_id for a in evento["asistentes"]):
                    eventos_inscrito.append({'fecha': clave_fecha, 'idx': idx, 'evento': evento})
    return eventos_inscrito

def obtener_eventos_creados_por(user_id: int, dias: int = 30) -> list:
    """Busca los eventos futuros creados por un usuario específico.

    Args:
        user_id (int): El ID de Telegram del creador del evento.
        dias (int, optional): El número de días hacia el futuro a buscar. Por defecto 30.

    Returns:
        list: Una lista de diccionarios, cada uno representando un evento
              creado por el usuario. Incluye fecha, índice y datos del evento.
    """
    eventos_creados = []
    hoy = datetime.today()
    for i in range(dias):
        fecha = hoy + timedelta(days=i)
        clave_fecha = fecha.strftime("%Y-%m-%d")
        if clave_fecha in agenda:
            for idx, evento in enumerate(agenda[clave_fecha]):
                if evento.get('activo', True) and evento.get('creador_id') == user_id:
                    eventos_creados.append({'fecha': clave_fecha, 'idx': idx, 'evento': evento})
    return eventos_creados