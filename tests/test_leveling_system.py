# tests/test_leveling_system.py
import pytest
from unittest.mock import patch, MagicMock, ANY, AsyncMock
from time import time

from src.config import levels
from src.managers import user_manager
from src.handlers import level_handlers

# --- Fixtures ---

@pytest.fixture(autouse=True)
def manage_users_db():
    """Fixture para limpiar la BBDD de usuarios antes y después de cada test."""
    user_manager.users_db.clear()
    yield
    user_manager.users_db.clear()

@pytest.fixture
def mock_user():
    """Crea un mock de un objeto User de Telegram."""
    user = MagicMock()
    user.id = 12345
    user.first_name = "Test"
    user.username = "testuser"
    user.is_bot = False
    return user

# --- Pruebas del user_manager ---

def test_update_user_activity_new_user(mock_user):
    """Verifica que un usuario nuevo se crea con los campos de nivel por defecto."""
    with patch('src.managers.user_manager.save_users') as mock_save:
        user_manager.update_user_activity(mock_user)
        
        mock_save.assert_called_once()
        user_data = user_manager.users_db[str(mock_user.id)]
        
        assert "level" in user_data
        assert user_data["level"] == 1
        assert "xp" in user_data
        assert user_data["xp"] == 0
        assert "last_xp_timestamp" in user_data

def test_grant_xp_cooldown(mock_user):
    """Verifica que la XP no se otorga si el cooldown no ha pasado."""
    with patch('src.managers.user_manager.save_users'):
        # 1. Damos XP inicial al usuario
        user_manager.update_user_activity(mock_user)
        user_manager.users_db[str(mock_user.id)]["last_xp_timestamp"] = time()
        
        # 2. Intentamos dar XP de nuevo inmediatamente
        level_up = user_manager.grant_xp_on_message(mock_user.id)
        
        # 3. Verificamos que no ha subido de nivel y la XP es la inicial
        assert level_up is None
        assert user_manager.users_db[str(mock_user.id)]["xp"] == 0

def test_grant_xp_and_level_up(mock_user):
    """Verifica que un usuario gana XP y sube de nivel."""
    with patch('src.managers.user_manager.save_users'):
        # 1. Creamos al usuario y forzamos su XP para que esté a punto de subir
        user_manager.update_user_activity(mock_user)
        
        xp_for_lvl_2 = levels.calculate_xp_for_level(2)
        
        user_manager.users_db[str(mock_user.id)]["xp"] = xp_for_lvl_2 - 10
        user_manager.users_db[str(mock_user.id)]["last_xp_timestamp"] = 0 # Reseteamos cooldown
        
        # 2. Otorgamos XP
        level_up_info = user_manager.grant_xp_on_message(mock_user.id)
        
        # 3. Verificamos que ha subido de nivel
        assert level_up_info is not None
        assert level_up_info["level_num"] == 2
        assert level_up_info["level_name"] == levels.LEVEL_NAMES[2]
        
        user_data = user_manager.users_db[str(mock_user.id)]
        assert user_data["level"] == 2
        assert user_data["xp"] == xp_for_lvl_2 + 10

def test_get_user_level_info(mock_user):
    """Verifica que la información de nivel se devuelve correctamente."""
    with patch('src.managers.user_manager.save_users'):
        user_manager.update_user_activity(mock_user)
        user_manager.users_db[str(mock_user.id)]["xp"] = 300 # XP para estar en nivel 2
        user_manager.users_db[str(mock_user.id)]["level"] = 2

        info = user_manager.get_user_level_info(mock_user.id)

        assert info["level"] == 2
        assert info["level_name"] == levels.LEVEL_NAMES[2]
        assert info["xp"] == 300
        assert info["xp_base_level"] == levels.calculate_xp_for_level(2)
        assert info["xp_next_level"] == levels.calculate_xp_for_level(3)

# --- Pruebas de los Handlers ---

@pytest.mark.asyncio
async def test_level_command_handler(mock_user):
    """Verifica que el comando /nivel funciona y envía el mensaje correcto."""
    with patch('src.managers.user_manager.save_users'):
        # 1. Preparamos el mock de Update y Context
        update = MagicMock()
        update.effective_user = mock_user
        update.effective_chat = MagicMock(type='private')
        update.message = AsyncMock()
        
        context = MagicMock()
        context.bot = AsyncMock()

        # 2. Creamos al usuario en la BBDD de prueba
        user_manager.update_user_activity(mock_user)
        
        # 3. Ejecutamos el handler
        await level_handlers.level_command(update, context)
        
        # 4. Verificamos que se envió un mensaje
        context.bot.send_message.assert_called_once()
        call_args, call_kwargs = context.bot.send_message.call_args
        
        assert "Tu Senda del Riojano" in call_kwargs["text"]
        assert "Nivel 1: Turista en la Laurel" in call_kwargs["text"]
        assert "░░░░░░░░░░" in call_kwargs["text"]
        assert call_kwargs["parse_mode"] == "Markdown"
