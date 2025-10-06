# tests/test_handlers.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.handlers import general_handlers, agenda_handlers
from src.managers import agenda_manager

# --- Mocks para los objetos de Telegram ---

@pytest.fixture
def mock_update_message():
    """Crea un mock de un objeto Update con un mensaje de texto."""
    update = MagicMock()
    update.effective_user = MagicMock(id=123, first_name="TestUser", username="test_user")
    update.message = AsyncMock()
    update.message.text = "/start"
    return update

@pytest.fixture
def mock_update_callback():
    """Crea un mock de un objeto Update con una callback query."""
    update = MagicMock()
    update.effective_user = MagicMock(id=123, first_name="TestUser", username="test_user")
    update.callback_query = AsyncMock()
    update.callback_query.from_user = update.effective_user
    return update

@pytest.fixture
def mock_context():
    """Crea un mock del objeto Context de PTB."""
    context = MagicMock()
    context.bot = AsyncMock()
    context.user_data = {}
    return context

# --- Pruebas de Integración para Handlers ---

@pytest.mark.asyncio
async def test_start_command(mock_update_message, mock_context):
    """Verifica que el comando /start responde con el mensaje correcto."""
    await general_handlers.start(mock_update_message, mock_context)
    # Verificamos que se llamó a reply_text
    mock_update_message.message.reply_text.assert_called_once()
    # Verificamos que el saludo está en el mensaje
    call_args = mock_update_message.message.reply_text.call_args
    assert "¡Aúpa, [TestUser]" in call_args[0][0]

@pytest.mark.asyncio
async def test_agenda_menu_command(mock_update_message, mock_context):
    """Verifica que el comando /agenda muestra el menú principal."""
    await agenda_handlers.agenda_menu(mock_update_message, mock_context)
    mock_update_message.message.reply_text.assert_called_once()
    call_args = mock_update_message.message.reply_text.call_args
    assert "¿Qué quieres hacer con la agenda?" in call_args[0][0]
    # Verificamos que el teclado tiene los botones correctos
    reply_markup = call_args[1]["reply_markup"]
    assert len(reply_markup.inline_keyboard) == 5 # 5 filas de botones
    assert reply_markup.inline_keyboard[0][0].text == "📅 Ver agenda"

@pytest.mark.asyncio
async def test_agenda_callback_ver_agenda_vacia(mock_update_callback, mock_context):
    """Verifica que el callback 'ver_agenda' muestra el mensaje correcto si no hay eventos."""
    mock_update_callback.callback_query.data = "ver_agenda"
    
    await agenda_handlers.main_agenda_callback_handler(mock_update_callback, mock_context)
    
    mock_update_callback.callback_query.edit_message_text.assert_called_once()
    call_args = mock_update_callback.callback_query.edit_message_text.call_args
    assert "No hay nada programado" in call_args[0][0]

@pytest.mark.asyncio
async def test_flujo_crear_evento_via_handlers(mock_update_callback, mock_context):
    """Simula el flujo completo de creación de un evento a través de los handlers."""
    # 1. Usuario pulsa "Crear un evento"
    mock_update_callback.callback_query.data = "crear_evento_fecha"
    await agenda_handlers.main_agenda_callback_handler(mock_update_callback, mock_context)
    mock_update_callback.callback_query.edit_message_text.assert_called_with(
        "PASO 1: Elige la fecha del evento.",
        reply_markup=pytest.ANY
    )

    # 2. Usuario selecciona una fecha
    fecha_seleccionada = "2025-10-26"
    mock_update_callback.callback_query.data = f"fecha_seleccionada|{fecha_seleccionada}"
    await agenda_handlers.main_agenda_callback_handler(mock_update_callback, mock_context)
    assert mock_context.user_data["nuevo_evento"]["fecha"] == fecha_seleccionada
    mock_update_callback.callback_query.edit_message_text.assert_called_with(
        "PASO 2: Ahora elige la hora.",
        reply_markup=pytest.ANY
    )

    # 3. Usuario selecciona una hora
    hora_seleccionada = "19:30"
    mock_update_callback.callback_query.data = f"hora_seleccionada|{hora_seleccionada}"
    await agenda_handlers.main_agenda_callback_handler(mock_update_callback, mock_context)
    assert mock_context.user_data["nuevo_evento"]["hora"] == hora_seleccionada
    assert mock_context.user_data["estado"] == "esperando_nombre_evento"
    mock_update_callback.callback_query.edit_message_text.assert_called_with(
        pytest.string_containing("Perfecto. Evento para el"),
        parse_mode="Markdown"
    )

    # 4. Usuario envía el nombre del evento por mensaje
    mock_msg_update = mock_update_message
    mock_msg_update.message.text = "Cena de prueba"
    # El estado se guarda en el contexto de la prueba anterior
    await agenda_handlers.manejar_mensajes_de_texto(mock_msg_update, mock_context)
    mock_msg_update.message.reply_text.assert_called_with("✅ ¡Evento guardado con éxito!")

    # Verificación final: el evento debe estar en la agenda
    eventos = agenda_manager.obtener_eventos_activos()
    assert len(eventos[fecha_seleccionada]) == 1
    assert eventos[fecha_seleccionada][0]["titulo"] == "Cena de prueba"
