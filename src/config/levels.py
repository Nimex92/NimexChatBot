# src/config/levels.py
"""
Configuración del sistema de niveles "La Senda del Riojano".
"""

# --- Parámetros de Progresión ---
XP_PER_MESSAGE = 20  # Puntos de experiencia ganados por mensaje (con cooldown)
XP_COOLDOWN_SECONDS = 60  # Segundos que deben pasar para volver a ganar XP

# --- Fórmula de XP por Nivel ---
# Usamos una fórmula exponencial para que los niveles altos requieran mucha más XP.
# Fórmula: XP_Requerida = BASE_XP * (NIVEL ** EXPONENTE)
BASE_XP = 100
EXPONENT = 1.5

def calculate_xp_for_level(level: int) -> int:
    """Calcula la XP total necesaria para alcanzar un nivel determinado."""
    if level <= 1:
        return 0
    return int(BASE_XP * (level ** EXPONENT))

# --- Definición de Niveles y sus Nombres ---
# El bot buscará el siguiente nivel en esta lista. Los saltos son intencionados.
LEVEL_NAMES = {
    1: "Turista en la Laurel",
    2: "Probando un 'Roto'",
    3: "Cliente Frecuente (¡Ya pide servilleta!)",
    5: "De Cuadrilla por San Juan",
    7: "Conoce los 'Modernos'",
    10: "Vendimiador Novato",
    15: "Experto en 'Claretes'",
    20: "Bodeguero",
    25: "Ha visto a Ezcaray en fiestas",
    30: "Riojano de Pura Cepa",
    40: "¡Disfrutando del 'Vino, y se fue'!",
    50: "¡RESERVA ESPECIAL! 🍷",
    60: "San Mateo (¡El Cohete!)"
}

# --- Generación de la Estructura de Datos de Niveles ---
# Creamos un diccionario completo con el número de nivel, nombre y la XP requerida.
LEVEL_THRESHOLDS = {
    level: {
        "name": name,
        "xp_required": calculate_xp_for_level(level)
    }
    for level, name in LEVEL_NAMES.items()
}

# Añadimos un nivel "máximo" para manejar la progresión más allá del último nivel definido.
# Buscamos el último nivel definido para usarlo como base.
last_defined_level = max(LEVEL_NAMES.keys())
LEVEL_THRESHOLDS[last_defined_level + 1] = {
    "name": LEVEL_NAMES[last_defined_level], # Repite el último nombre o uno genérico
    "xp_required": float('inf') # Un valor infinito para que no se pueda superar
}

def get_level_for_xp(xp: int) -> tuple[int, str]:
    """Devuelve el nivel y el nombre correspondientes a una cantidad de XP."""
    current_level_num = 1
    current_level_name = LEVEL_NAMES[1]

    # Iteramos sobre los niveles ordenados para encontrar en cuál encaja la XP.
    for level_num, data in sorted(LEVEL_THRESHOLDS.items()):
        if xp >= data["xp_required"]:
            current_level_num = level_num
            current_level_name = data["name"]
        else:
            break # Si no superamos el umbral de XP, nos quedamos en el nivel anterior.
            
    return current_level_num, current_level_name

def get_next_level_xp(level: int) -> int | None:
    """Devuelve la XP necesaria para el siguiente nivel definido."""
    # Encuentra el siguiente nivel en la secuencia ordenada de claves.
    sorted_levels = sorted(LEVEL_NAMES.keys())
    try:
        current_index = sorted_levels.index(level)
        next_level_num = sorted_levels[current_index + 1]
        return LEVEL_THRESHOLDS[next_level_num]["xp_required"]
    except (ValueError, IndexError):
        # Si el nivel actual no está o es el último, no hay siguiente nivel.
        return None
