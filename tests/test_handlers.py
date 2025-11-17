# tests/test_handlers.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.handlers import general_handlers, agenda_handlers, debate_handlers
from src.managers import agenda_manager
from src.config import settings
from telegram.constants import ChatMemberStatus

# --- Mocks para los objetos de Telegram ---

@pytest.fixture
def mock_update_message():
    """Crea un mock de un objeto Update con un mensaje de texto."""
    update = MagicMock()
    update.effective_user = MagicMock(id=123, first_name="TestUser", username="test_user")
    update.effective_chat = MagicMock(id=settings.GROUP_CHAT_ID)
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
@patch('src.handlers.debate_handlers.debate_manager', new_callable=AsyncMock)
async def test_force_debate_command_admin(mock_debate_manager, mock_update_message, mock_context):
    """Verifica que un admin puede forzar un debate."""
    # 1. Configuración: El usuario es admin
    mock_admin = MagicMock()
    mock_admin.status = ChatMemberStatus.ADMINISTRATOR
    mock_context.bot.get_chat_member.return_value = mock_admin
    mock_debate_manager.send_and_pin_debate.return_value = "¡Nuevo debate forzado!"

    # 2. Ejecución
    await debate_handlers.force_debate_command(mock_update_message, mock_context)

    # 3. Verificación
    mock_context.bot.get_chat_member.assert_called_once_with(settings.GROUP_CHAT_ID, 123)
    mock_update_message.message.reply_text.assert_any_call("✅ Entendido. Forzando un nuevo debate...")
    mock_debate_manager.unpin_previous_debate.assert_called_once()
    mock_debate_manager.send_and_pin_debate.assert_called_once()
    mock_update_message.message.reply_text.assert_called_with("¡Nuevo debate forzado!")

@pytest.mark.asyncio
@patch('src.handlers.debate_handlers.debate_manager', new_callable=AsyncMock)
async def test_force_debate_command_non_admin(mock_debate_manager, mock_update_message, mock_context):
    """Verifica que un usuario normal no puede forzar un debate."""
    # 1. Configuración: El usuario es un miembro normal
    mock_member = MagicMock()
    mock_member.status = ChatMemberStatus.MEMBER
    mock_context.bot.get_chat_member.return_value = mock_member

    # 2. Ejecución
    await debate_handlers.force_debate_command(mock_update_message, mock_context)

    # 3. Verificación
    mock_context.bot.get_chat_member.assert_called_once_with(settings.GROUP_CHAT_ID, 123)
    mock_update_message.message.reply_text.assert_called_once_with("⚠️ Solo los administradores pueden usar este comando.")
    mock_debate_manager.unpin_previous_debate.assert_not_called()
    mock_debate_manager.send_and_pin_debate.assert_not_called()