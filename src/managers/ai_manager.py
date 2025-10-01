# src/managers/ai_manager.py
"""Módulo de interacción con el modelo de Inteligencia Artificial.

Este módulo se encarga de:
1.  Configurar el modelo de IA (Gemini) con un `system_instruction` que define
    su personalidad y comportamiento.
2.  Proporcionar al modelo una lista de herramientas (funciones) que puede utilizar.
3.  Orquestar el flujo de conversación, manejando las llamadas a funciones
    que el modelo solicita y devolviéndole los resultados hasta obtener una
    respuesta final en texto.
"""
from src.config import settings
from src.ai_tools import ALL_TOOLS, AVAILABLE_TOOLS
import google.generativeai as genai
from datetime import datetime
import traceback

# Instancia global del modelo de IA (Gemini), configurado con su personalidad y herramientas.
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=ALL_TOOLS,
    system_instruction=(
        "Eres un asistente para un bot de Telegram, ¡pero no uno cualquiera! Eres de La Rioja, súper majo, y te encanta ayudar a la gente a organizar sus planes. 🍇"
        f"La fecha y hora actual es {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
        "Tu objetivo es ayudar al usuario a gestionar su agenda de eventos. Eres cercano, un poco informal y siempre positivo."
        "\n\n"
        "**REGLAS DE COMPORTAMIENTO Y ESTILO:**\n"
        "1. **¡Usa muchos emojis!** 🎉📅🥳 Tus respuestas tienen que ser visuales y alegres.\n"
        "2. **Habla con un toque riojano.** Usa expresiones como '¡Aúpa!', 'majo/a', '¡qué hermosura!', 'no te preocupes, que esto lo apañamos en un periquete'.\n"
        "3. **Sé siempre servicial y directo.** Vas al grano pero con simpatía, como si hablaras con un amigo en la calle Laurel.\n"
        "4. **Formatea las listas de eventos** de forma clara. Empieza con un resumen y luego lista los eventos con un guion, así:\n"
        "   ```\n"
        "   ¡Aúpa! Pues para esta semana he encontrado 2 quedadas majas:\n"
        "   - 🍷 20:00 - Pinchopote por la Laurel\n"
        "   - ⚽ 19:00 - Partido en Las Gaunas\n"
        "   ```"
    )
)

async def process_user_prompt(prompt: str, user_id: int) -> str:
    """Procesa el texto de un usuario utilizando el modelo de IA Gemini.

    Esta función orquesta la interacción con el modelo de IA. Envía el prompt
    del usuario y, si el modelo decide que necesita usar una de las herramientas
    definidas (como `crear_evento`), esta función ejecuta la herramienta
    correspondiente y devuelve el resultado al modelo. Este proceso puede
    repetirse hasta que el modelo genere una respuesta de texto final para el
    usuario.

    Args:
        prompt (str): El mensaje de texto enviado por el usuario.
        user_id (int): El ID de Telegram del usuario que envía el mensaje.

    Returns:
        str: La respuesta de texto final generada por la IA, o un mensaje
             de error si ocurre un problema durante el proceso.
    """
    if not settings.GEMINI_API_KEY:
        return "La integración con la IA no está configurada (falta la API Key de Gemini)."
        
    try:
        chat = model.start_chat()
        contextual_prompt = f"El usuario con ID {user_id} pide lo siguiente: {prompt}"
        
        response = await chat.send_message_async(contextual_prompt)

        while True:
            part = response.candidates[0].content.parts[0]
            
            if not part.function_call:
                return response.text

            function_call = part.function_call
            function_name = function_call.name
            function_args = {key: value for key, value in function_call.args.items()}
            
            if function_name in AVAILABLE_TOOLS:
                function_to_call = AVAILABLE_TOOLS[function_name]
                print(f"🤖 Ejecutando herramienta: {function_name}({function_args})")
                
                # La función real se ejecuta aquí
                function_response_data = function_to_call(**function_args)
                
                # Enviamos el resultado de vuelta a la IA
                response = await chat.send_message_async(
                    [
                        {
                            "function_response": {
                                "name": function_name,
                                "response": {
                                    "result": str(function_response_data),
                                }
                            }
                        }
                    ]
                )
            else:
                return "Lo siento, majo, la IA ha intentado usar una herramienta que no conozco."

    except Exception as e:
        print("🚨 ¡Leñe! Error en el flujo de IA. El traceback completo es:")
        traceback.print_exc()
        return f"¡Ay va! Ha habido un problemilla técnico al procesar tu petición. Detalles: {e}"