# tests/test_debate_manager.py
import pytest
import json
from unittest.mock import patch, mock_open, AsyncMock

# Asumimos que los tests se corren desde la raíz del proyecto
from src.managers import debate_manager

# Usamos pytest-asyncio para marcar los tests asíncronos
@pytest.mark.asyncio
async def test_generate_debate_topic():
    """
    Verifica que la función para generar debates llame a la IA
    y devuelva el texto limpio.
    """
    # 1. Preparamos el Mock de la función de IA
    # La IA nos devolverá un texto con espacios y asteriscos
    mock_ai_response = "  *¿Es el gazpacho una sopa o una ensalada líquida?*   "
    
    # Usamos patch para reemplazar 'generate_text' en el módulo 'debate_manager'
    with patch('src.managers.debate_manager.generate_text', new_callable=AsyncMock) as mock_generate_text:
        # Configuramos el mock para que devuelva nuestro texto cuando se le llame
        mock_generate_text.return_value = mock_ai_response
        
        # 2. Ejecutamos la función que queremos probar
        topic = await debate_manager.generate_debate_topic()
        
        # 3. Verificamos los resultados
        # Aseguramos que se llamó a la función de IA con el prompt correcto
        mock_generate_text.assert_called_once_with(debate_manager.DEBATE_PROMPT)
        
        # Aseguramos que el texto devuelto está limpio (sin espacios extra ni asteriscos)
        expected_topic = "¿Es el gazpacho una sopa o una ensalada líquida?"
        assert topic == expected_topic

def test_save_and_load_debate_data(tmp_path):
    """
    Verifica que los datos del debate se guardan y cargan correctamente.
    Usa un directorio temporal (tmp_path) para no tocar el archivo real.
    """
    # 1. Preparamos el entorno del test
    # Creamos un archivo de datos falso en el directorio temporal
    temp_file = tmp_path / "debate.json"
    
    # Datos que vamos a guardar y luego cargar
    test_data = {"last_message_id": 12345}
    
    # Usamos patch para que settings.DEBATE_FILE apunte a nuestro archivo temporal
    with patch('src.managers.debate_manager.settings.DEBATE_FILE', str(temp_file)):
        # 2. Ejecutamos las funciones
        # Guardamos los datos iniciales
        with open(temp_file, 'w') as f:
            json.dump(test_data, f)
        
        # Cargamos los datos a la variable global del manager
        debate_manager.load_debate_data()
        
        # 3. Verificamos
        # Comprobamos que los datos en memoria son los correctos
        assert debate_manager.debate_data == test_data
        
        # Ahora probamos el guardado
        new_data = {"last_message_id": 67890}
        debate_manager.debate_data = new_data
        debate_manager.save_debate_data()
        
        # Leemos el archivo para ver si se guardó bien
        with open(temp_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == new_data

def test_get_and_set_last_debate_message_id():
    """
    Verifica que podemos obtener y establecer el ID del último mensaje.
    """
    # 1. Preparamos el estado inicial
    # Simulamos que no hay ningún ID guardado
    debate_manager.debate_data = {}
    
    # 2. Verificamos el estado inicial
    assert debate_manager.get_last_debate_message_id() is None
    
    # 3. Ejecutamos la función para establecer el ID
    # Usamos patch para evitar que se escriba en un archivo real durante el test
    with patch('src.managers.debate_manager.save_debate_data') as mock_save:
        debate_manager.set_last_debate_message_id(98765)
        
        # 4. Verificamos el nuevo estado
        assert debate_manager.get_last_debate_message_id() == 98765
        
        # Aseguramos que se intentó guardar el cambio
        mock_save.assert_called_once()
        
        # Probamos a borrarlo
        debate_manager.set_last_debate_message_id(None)
        assert debate_manager.get_last_debate_message_id() is None
