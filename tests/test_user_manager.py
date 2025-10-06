# tests/test_user_manager.py
import pytest
from src.managers import user_manager
from datetime import datetime, timedelta
from types import SimpleNamespace

# --- Mocks y Fixtures adicionales ---

class MockBot:
    """Un mock simple para simular el bot de Telegram y sus métodos."""
    def __init__(self):
        self.kicked_users = []
        self.unbanned_users = []
        self.sent_messages = {}

    async def kick_chat_member(self, chat_id, user_id):
        self.kicked_users.append(user_id)
        return True

    async def unban_chat_member(self, chat_id, user_id):
        self.unbanned_users.append(user_id)
        return True

    async def send_message(self, chat_id, text):
        self.sent_messages.setdefault(chat_id, []).append(text)
        return True

@pytest.fixture
def mock_context():
    """Crea un mock del objeto Context de PTB con un bot simulado."""
    context = SimpleNamespace()
    context.bot = MockBot()
    return context

# --- Pruebas para la lógica de usuarios ---

def test_update_user_activity_nuevo_usuario():
    """Verifica que un usuario nuevo se añade correctamente a la BBDD."""
    user = SimpleNamespace(id=111, first_name="Nuevo", username="nuevo_user")
    
    user_manager.update_user_activity(user)

    assert "111" in user_manager.users_db
    db_user = user_manager.users_db["111"]
    assert db_user["first_name"] == "Nuevo"
    assert db_user["lives"] == 3
    assert "last_seen" in db_user

def test_update_user_activity_usuario_existente():
    """Verifica que la actividad de un usuario existente se actualiza."""
    user = SimpleNamespace(id=222, first_name="Viejo", username="viejo_user")
    
    # Primera actividad
    user_manager.update_user_activity(user)
    last_seen_1 = user_manager.users_db["222"]["last_seen"]

    # Segunda actividad (simulada un poco después)
    user_manager.update_user_activity(user)
    last_seen_2 = user_manager.users_db["222"]["last_seen"]

    assert last_seen_2 > last_seen_1

@pytest.mark.asyncio
async def test_check_inactivity_job_sin_inactivos(mock_context):
    """Verifica que el job no hace nada si todos los usuarios están activos."""
    user = SimpleNamespace(id=333, first_name="Activo", username="activo_user")
    user_manager.update_user_activity(user)

    await user_manager.check_inactivity_job(mock_context)

    assert len(mock_context.bot.kicked_users) == 0
    assert user_manager.users_db["333"]["lives"] == 3

@pytest.mark.asyncio
async def test_check_inactivity_job_resta_una_vida(mock_context, monkeypatch):
    """Verifica que un usuario inactivo pierde una vida."""
    user_id_str = "444"
    user = SimpleNamespace(id=int(user_id_str), first_name="Inactivo", username="inactivo_user")
    user_manager.update_user_activity(user)

    # Simulamos que el tiempo ha pasado
    inactivity_days = user_manager.settings.INACTIVITY_DAYS
    fake_now = datetime.now() + timedelta(days=inactivity_days + 1)
    monkeypatch.setattr("src.managers.user_manager.datetime", SimpleNamespace(now=lambda: fake_now))

    await user_manager.check_inactivity_job(mock_context)

    assert user_manager.users_db[user_id_str]["lives"] == 2
    # Verificamos que se le notificó
    assert int(user_id_str) in mock_context.bot.sent_messages

@pytest.mark.asyncio
async def test_check_inactivity_job_expulsa_usuario(mock_context, monkeypatch):
    """Verifica que un usuario sin vidas es expulsado."""
    user_id_str = "555"
    user = SimpleNamespace(id=int(user_id_str), first_name="Expulsado", username="expulsado_user")
    user_manager.update_user_activity(user)
    user_manager.users_db[user_id_str]["lives"] = 1 # Solo le queda una vida

    # Simulamos que el tiempo ha pasado
    inactivity_days = user_manager.settings.INACTIVITY_DAYS
    fake_now = datetime.now() + timedelta(days=inactivity_days + 1)
    monkeypatch.setattr("src.managers.user_manager.datetime", SimpleNamespace(now=lambda: fake_now))

    await user_manager.check_inactivity_job(mock_context)

    # Verificaciones
    assert user_manager.users_db[user_id_str]["lives"] == 0
    assert int(user_id_str) in mock_context.bot.kicked_users
    assert int(user_id_str) in mock_context.bot.unbanned_users
