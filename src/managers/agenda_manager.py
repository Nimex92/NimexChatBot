# src/managers/agenda_manager.py
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta
from babel.dates import format_datetime
import locale
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

# Importamos la ruta del archivo desde nuestra configuración centralizada
from src.config import settings
from src.managers import user_manager

# El estado de la agenda (la variable) vive y se gestiona únicamente aquí
agenda = defaultdict(list)

def cargar_agenda():
    """Carga la agenda desde el archivo JSON al iniciar el bot."""
    global agenda
    try:
        # Asegurarse de que el directorio de datos exista
        os.makedirs(os.path.dirname(settings.AGENDA_FILE), exist_ok=True)
        
        with open(settings.AGENDA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for fecha, eventos in data.items():
                agenda[fecha] = eventos
            print(f"✅ Agenda cargada desde {settings.AGENDA_FILE}")
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"❌ No se encontró {settings.AGENDA_FILE} o está dañado. Se usará una agenda vacía.")
        agenda = defaultdict(list)

def guardar_agenda():
    """Guarda el estado actual de la agenda en el archivo JSON."""
    with open(settings.AGENDA_FILE, "w", encoding="utf-8") as f:
        json.dump(agenda, f, indent=2, ensure_ascii=False)
    print("💾 Agenda guardada.")

# --- API interna para manipular la agenda ---

def crear_evento(fecha: str, hora: str, titulo: str, creador_id: int):
    """Añade un nuevo evento a la agenda y lo guarda."""
    evento = {
        "hora": hora,
        "titulo": titulo,
        "asistentes": [],
        "creador_id": creador_id,
        "activo": True
    }
    agenda[fecha].append(evento)
    guardar_agenda()

def desactivar_evento(fecha: str, idx: int):
    """Marca un evento como inactivo (borrado lógico)."""
    if fecha in agenda and len(agenda[fecha]) > idx:
        agenda[fecha][idx]['activo'] = False
        guardar_agenda()
        return agenda[fecha][idx]
    return None

def inscribir_usuario(fecha: str, idx: int, user_info: dict):
    """Inscribe un usuario a un evento, evitando duplicados."""
    evento = agenda[fecha][idx]
    if not any(a.get("id") == user_info["id"] for a in evento["asistentes"]):
        evento["asistentes"].append(user_info)
        guardar_agenda()

        from types import SimpleNamespace
        user_obj = SimpleNamespace(**user_info)
        user_manager.update_user_activity(user_obj)

        return True
    return False

def desinscribir_usuario(fecha: str, idx: int, user_id: int):
    """Da de baja a un usuario de un evento."""
    evento = agenda[fecha][idx]
    asistentes_antes = len(evento["asistentes"])
    evento["asistentes"] = [a for a in evento["asistentes"] if a.get("id") != user_id]
    if len(evento["asistentes"]) < asistentes_antes:
        guardar_agenda()
        return True
    return False

# --- Funciones para obtener datos de la agenda ---

# src/managers/agenda_manager.py
# ... (imports) ...

def obtener_eventos_activos(fecha_inicio: str = None, fecha_fin: str = None):
    """
    Devuelve un DICCIONARIO de eventos activos.
    Si se especifican fechas, busca en ese rango. Si no, en los próximos 14 días.
    """
    eventos_por_fecha = {}
    hoy = datetime.today().date()

    if fecha_inicio and fecha_fin:
        try:
            start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            dias_a_buscar = (end_date - start_date).days + 1
            fechas = [start_date + timedelta(days=i) for i in range(dias_a_buscar)]
        except ValueError:
            return {} # Devuelve un diccionario vacío si las fechas son incorrectas
    else:
        fechas = [hoy + timedelta(days=i) for i in range(14)]

    for fecha in fechas:
        clave_fecha = fecha.strftime("%Y-%m-%d")
        if clave_fecha in agenda:
            eventos_activos = [e for e in agenda[clave_fecha] if e.get('activo', True)]
            if eventos_activos:
                eventos_por_fecha[clave_fecha] = eventos_activos

    return eventos_por_fecha # <-- Devuelve el diccionario con los datos

def obtener_eventos_inscrito(user_id: int, dias: int = 30):
    """Devuelve los eventos en los que un usuario está inscrito."""
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

def obtener_eventos_creados_por(user_id: int, dias: int = 30):
    """Devuelve los eventos creados por un usuario."""
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