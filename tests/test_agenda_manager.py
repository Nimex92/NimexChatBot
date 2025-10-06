# tests/test_agenda_manager.py
from src.managers import agenda_manager
from datetime import datetime, timedelta

# --- Pruebas para la lógica de la agenda ---

def test_crear_evento():
    """Verifica que un evento se crea y se guarda correctamente."""
    # Preparamos los datos
    fecha = datetime.now().strftime("%Y-%m-%d")
    hora = "10:00"
    titulo = "Reunión de prueba"
    creador_id = 12345

    # Llamamos a la función
    agenda_manager.crear_evento(fecha, hora, titulo, creador_id)

    # Verificamos el resultado
    eventos = agenda_manager.obtener_eventos_activos()
    assert len(eventos[fecha]) == 1
    evento_creado = eventos[fecha][0]
    assert evento_creado["titulo"] == titulo
    assert evento_creado["hora"] == hora
    assert evento_creado["creador_id"] == creador_id
    assert evento_creado["activo"] is True

def test_inscribir_usuario():
    """Verifica que un usuario puede inscribirse y no puede duplicarse."""
    fecha = datetime.now().strftime("%Y-%m-%d")
    agenda_manager.crear_evento(fecha, "11:00", "Evento de inscripción", 123)
    user_info = {"id": 987, "nombre": "Tester", "username": "tester_user"}

    # Primera inscripción (debería funcionar)
    resultado1 = agenda_manager.inscribir_usuario(fecha, 0, user_info)
    assert resultado1 is True

    eventos = agenda_manager.obtener_eventos_activos()
    asistentes = eventos[fecha][0]["asistentes"]
    assert len(asistentes) == 1
    assert asistentes[0]["id"] == 987

    # Segunda inscripción (no debería añadir al usuario de nuevo)
    resultado2 = agenda_manager.inscribir_usuario(fecha, 0, user_info)
    assert resultado2 is False
    assert len(asistentes) == 1 # Sigue habiendo solo 1 asistente

def test_desinscribir_usuario():
    """Verifica que un usuario puede darse de baja de un evento."""
    fecha = datetime.now().strftime("%Y-%m-%d")
    user_info = {"id": 555, "nombre": "Borrame", "username": "borrame_user"}
    agenda_manager.crear_evento(fecha, "12:00", "Evento de baja", 123)
    agenda_manager.inscribir_usuario(fecha, 0, user_info)

    # Verificamos que está inscrito
    eventos = agenda_manager.obtener_eventos_activos()
    assert len(eventos[fecha][0]["asistentes"]) == 1

    # Lo damos de baja
    resultado = agenda_manager.desinscribir_usuario(fecha, 0, 555)
    assert resultado is True

    # Verificamos que ya no está
    eventos_actualizados = agenda_manager.obtener_eventos_activos()
    assert len(eventos_actualizados[fecha][0]["asistentes"]) == 0

def test_desactivar_evento():
    """Verifica que un evento se marca como inactivo (borrado lógico)."""
    fecha = datetime.now().strftime("%Y-%m-%d")
    agenda_manager.crear_evento(fecha, "13:00", "Evento a eliminar", 123)

    # Verificamos que el evento existe
    assert len(agenda_manager.obtener_eventos_activos()) == 1

    # Lo desactivamos
    agenda_manager.desactivar_evento(fecha, 0)

    # Verificamos que ya no aparece en los eventos activos
    assert len(agenda_manager.obtener_eventos_activos()) == 0
