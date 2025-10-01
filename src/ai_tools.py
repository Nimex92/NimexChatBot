# src/ai_tools.py
"""Define las herramientas (funciones) que el modelo de IA puede utilizar.

Este módulo cumple dos propósitos principales:
1.  **ALL_TOOLS**: Define la estructura y descripción de las herramientas en un
    formato que el modelo de IA (Gemini) puede entender. Esto incluye el nombre
    de la función, su propósito y el esquema de sus parámetros.
2.  **AVAILABLE_TOOLS**: Mapea los nombres de las herramientas definidas a las
    funciones de Python reales que se encuentran en los módulos de `managers`.
"""
from src.managers import agenda_manager
from datetime import datetime

# Define la estructura de las herramientas que el modelo de IA puede usar.
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
        # --- DESCRIPCIÓN MEJORADA ---
        "description": "Consulta eventos en la agenda. Puede buscar en un rango de fechas específico o, si no se especifica, devuelve los eventos de las próximas 2 semanas.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                # --- NUEVOS PARÁMETROS OPCIONALES ---
                "fecha_inicio": {
                    "type": "STRING",
                    "description": f"Opcional. La fecha de inicio del rango de búsqueda, en formato AAAA-MM-DD. Hoy es {datetime.now().strftime('%Y-%m-%d')}."
                },
                "fecha_fin": {
                    "type": "STRING",
                    "description": "Opcional. La fecha de fin del rango de búsqueda, en formato AAAA-MM-DD."
                }
            }
            # No hay "required", por lo que son opcionales
        }
    }
]

# Mapea los nombres de las herramientas a las funciones reales de Python.
AVAILABLE_TOOLS = {
    "crear_evento": agenda_manager.crear_evento,
    "obtener_eventos_activos": agenda_manager.obtener_eventos_activos,
}