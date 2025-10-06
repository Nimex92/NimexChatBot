# src/ai_tools.py
from src.managers import agenda_manager
from datetime import datetime
import requests
import json
import os

# --- Implementación de la nueva herramienta del tiempo ---

def get_weather(ciudad: str):
    """
    Obtiene el tiempo actual para una ciudad. Primero la geocodifica y luego
    busca la previsión meteorológica.
    """
    try:
        # 1. Geocodificar la ciudad para obtener latitud y longitud
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={ciudad}&count=1&language=es&format=json"
        geo_response = requests.get(geo_url)
        geo_data = geo_response.json()
        
        if not geo_data.get("results"):
            return json.dumps({"error": f"No encontré la ciudad '{ciudad}'. ¿Está bien escrita?"})

        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        nombre_real = location["name"]

        # 2. Obtener el tiempo para esas coordenadas
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()

        # 3. Devolver los datos del tiempo en un formato que la IA pueda interpretar
        return json.dumps({
            "ciudad": nombre_real,
            "temperatura": weather_data["current_weather"]["temperature"],
            "viento": weather_data["current_weather"]["windspeed"],
            "codigo_tiempo": weather_data["current_weather"]["weathercode"]
        })
    except Exception as e:
        return json.dumps({"error": f"Hubo un problema técnico al buscar el tiempo: {str(e)}"})

def read_documentation_file(filename: str):
    """
    Lee el contenido de un archivo de documentación.
    """
    try:
        # Construimos la ruta completa al archivo en el directorio de documentos
        docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
        file_path = os.path.join(docs_dir, filename)

        # Verificamos que el archivo exista para evitar errores
        if not os.path.exists(file_path):
            return json.dumps({"error": f"El archivo '{filename}' no existe."})

        # Leemos y devolvemos el contenido del archivo
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    except Exception as e:
        return json.dumps({"error": f"Hubo un problema al leer el archivo: {str(e)}"})

# --- Definición de herramientas para Gemini ---

ALL_TOOLS = [
    {
        "name": "crear_evento",
        "description": "Crea un nuevo evento en la agenda para una fecha, hora y título específicos.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "fecha": {
                    "type": "STRING",
                    "description": f"La fecha del evento en formato AAAA-MM-DD. Hoy es {datetime.now().strftime('%Y-%m-%d')}."
                },
                "hora": {
                    "type": "STRING",
                    "description": "La hora del evento en formato HH:MM de 24 horas. Ejemplo: 'las 8 de la tarde' es '20:00'."
                },
                "titulo": {
                    "type": "STRING",
                    "description": "El nombre o descripción del evento, por ejemplo, 'Cena con amigos'."
                },
                "creador_id": {
                    "type": "INTEGER",
                    "description": "El ID numérico del usuario que está creando el evento."
                }
            },
            "required": ["fecha", "hora", "titulo", "creador_id"]
        }
    },
    {
        "name": "obtener_eventos_activos",
        "description": "Consulta eventos en la agenda. Puede buscar en un rango de fechas específico o, si no se especifica, devuelve los eventos de las próximas 2 semanas.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "fecha_inicio": {
                    "type": "STRING",
                    "description": f"Opcional. La fecha de inicio del rango de búsqueda, en formato AAAA-MM-DD. Hoy es {datetime.now().strftime('%Y-%m-%d')}."
                },
                "fecha_fin": {
                    "type": "STRING",
                    "description": "Opcional. La fecha de fin del rango de búsqueda, en formato AAAA-MM-DD."
                }
            }
        }
    },
    {
        "name": "get_weather",
        "description": "Obtiene el tiempo actual (temperatura, viento, etc.) para una ciudad específica.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "ciudad": {
                    "type": "STRING",
                    "description": "El nombre de la ciudad sobre la que se quiere consultar el tiempo. Por ejemplo, 'Logroño'."
                }
            },
            "required": ["ciudad"]
        }
    },
    {
        "name": "read_documentation_file",
        "description": "Lee el contenido de un archivo de documentación, como las normas de convivencia.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "filename": {
                    "type": "STRING",
                    "description": "El nombre del archivo a leer del directorio de documentación. Por ejemplo, 'normas_convivencia.md'."
                }
            },
            "required": ["filename"]
        }
    }
]

# --- Mapeo de herramientas a funciones de Python ---

AVAILABLE_TOOLS = {
    "crear_evento": agenda_manager.crear_evento,
    "obtener_eventos_activos": agenda_manager.obtener_eventos_activos,
    "get_weather": get_weather,
    "read_documentation_file": read_documentation_file,
}
