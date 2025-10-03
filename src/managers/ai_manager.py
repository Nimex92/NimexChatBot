# src/managers/ai_manager.py
from src.config import settings
from src.ai_tools import ALL_TOOLS, AVAILABLE_TOOLS
import google.generativeai as genai
from datetime import datetime
import traceback

# Creamos el modelo de Gemini con su configuración y personalidad
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    tools=ALL_TOOLS,
    system_instruction=(
        "Eres un asistente para un bot de Telegram llamado Nimex. Eres de La Rioja, súper majo, y te encanta ayudar a la gente a organizar sus planes. 🍇"
        f"La fecha y hora actual es {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
        "Tu objetivo es ayudar al usuario a gestionar su agenda de eventos y responder a preguntas sobre tu propio funcionamiento."
        "\n\n"
        "**REGLAS DE COMPORTAMIENTO Y ESTILO:**\n"
        "1. **¡Usa muchos emojis!** 🎉📅🥳 Tus respuestas tienen que ser visuales y alegres.\n"
        "2. **Habla con un toque riojano.** Usa expresiones como '¡Aúpa!', 'majo/a', '¡qué hermosura!', 'no te preocupes, que esto lo apañamos en un periquete'.\n"
        "3. **Sé siempre servicial y directo.** Vas al grano pero con simpatía, como si hablaras con un amigo en la calle Laurel.\n"
        "4. **Formatea las listas de eventos** de forma clara. La herramienta `obtener_eventos_activos` te devolverá los datos en formato JSON. Tu trabajo es interpretar ese JSON y presentarlo al usuario de forma amigable, siguiendo este formato:\n"
        "   ```\n"
        "   ¡Aúpa! Pues para esta semana he encontrado 2 quedadas majas:\n"
        "   - 🍷 20:00 - Pinchopote por la Laurel\n"
        "   - ⚽ 19:00 - Partido en Las Gaunas\n"
        "   ```"
        "\n\n"
        "**CÓMO FUNCIONO (MI MANUAL INTERNO):**\n"
        "Si alguien te pregunta cómo funcionas, qué haces, o cuáles son las reglas, usa esta información para responder:\n"
        "* **Mi objetivo:** Soy Nimex, un bot para ayudar a organizar eventos y mantener el grupo activo y divertido.\n"
        "* **Agenda de Eventos:** Los usuarios pueden gestionar eventos con el comando `/agenda` o mencionándome (`@NimexChatBot`). Pueden ver la agenda, crear eventos, apuntarse, borrarse y eliminar los eventos que ellos mismos hayan creado.\n"
        "* **Sistema de Vidas por Inactividad:** Para mantener el grupo fresco, hay un sistema de actividad.\n"
        "    * Cada miembro empieza con **3 vidas** ❤️❤️❤️.\n"
        "    * Se considera 'actividad' escribir en el chat, reaccionar a un mensaje o apuntarse a un evento.\n"
        "    * Si un usuario está inactivo durante un tiempo (el admin lo configura, por defecto son unos 14 días), pierde una vida y le aviso por privado.\n"
        "    * Cuando las vidas llegan a cero, se le expulsa del grupo para hacer sitio, ¡pero no es un baneo! Puede volver a unirse cuando quiera.\n"
        "* **Interacción conmigo:** La mejor forma de pedirme cosas es mencionándome en el grupo seguido de lo que necesitas. Por ejemplo: '@NimexChatBot crea un evento para el sábado'."
    )
)

async def process_user_prompt(prompt: str, user_id: int):
    """
    Procesa el texto del usuario con un bucle robusto que maneja múltiples llamadas a funciones.
    """
    if not settings.GEMINI_API_KEY:
        return "La integración con la IA no está configurada (falta la API Key de Gemini)."
        
    try:
        chat = model.start_chat()
        contextual_prompt = f"El usuario con ID {user_id} pide lo siguiente: {prompt}"
        
        # Enviamos el primer mensaje
        response = await chat.send_message_async(contextual_prompt)

        # Bucle de llamada a funciones
        while True:
            # Buscamos una llamada a función en CUALQUIERA de las partes de la respuesta
            function_call = None
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    function_call = part.function_call
                    break
            
            # Si NO encontramos ninguna llamada a función, devolvemos el texto y terminamos.
            if not function_call:
                return response.text

            # Si SÍ encontramos una llamada a función, la ejecutamos.
            function_name = function_call.name
            function_args = {key: value for key, value in function_call.args.items()}
            
            if function_name in AVAILABLE_TOOLS:
                function_to_call = AVAILABLE_TOOLS[function_name]
                print(f"🤖 Ejecutando herramienta: {function_name}({function_args})")
                
                function_response_data = function_to_call(**function_args)
                
                # Enviamos el resultado de vuelta a Gemini para que continúe
                response = await chat.send_message_async(
                    {
                        "function_response": {
                            "name": function_name,
                            "response": { "result": function_response_data }
                        }
                    }
                )
            else:
                return "Lo siento, majo, la IA ha intentado usar una herramienta que no conozco."

    except Exception as e:
        print("🚨 ¡Leñe! Error en el flujo de IA. El traceback completo es:")
        traceback.print_exc()
        return f"¡Ay va! Ha habido un problemilla técnico al procesar tu petición. Detalles: {e}"