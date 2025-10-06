# tests/conftest.py
import pytest
import os

@pytest.fixture(autouse=True)
def setup_and_teardown_test_data(monkeypatch):
    """
    Esta fixture se ejecuta automáticamente para cada prueba.
    Crea un directorio de datos temporal y redirige las rutas de los
    managers para que usen este directorio.
    """
    # 1. Definir un directorio de datos para las pruebas
    test_data_dir = "tests/test_data"
    os.makedirs(test_data_dir, exist_ok=True)

    test_agenda_file = os.path.join(test_data_dir, "agenda.json")
    test_users_file = os.path.join(test_data_dir, "users.json")

    # 2. Usar monkeypatch para que los managers usen las rutas de prueba
    monkeypatch.setattr("src.config.settings.AGENDA_FILE", test_agenda_file)
    monkeypatch.setattr("src.config.settings.USERS_FILE", test_users_file)

    # 3. El código de la prueba se ejecuta aquí (gracias a 'yield')
    yield

    # 4. Limpieza: eliminar los archivos creados después de cada prueba
    if os.path.exists(test_agenda_file):
        os.remove(test_agenda_file)
    if os.path.exists(test_users_file):
        os.remove(test_users_file)
