# src/managers/ai_manager.py
from src.config import settings
from src.ai_tools import ALL_TOOLS, AVAILABLE_TOOLS
import google.generativeai as genai
from datetime import datetime
import traceback

# Creamos el modelo de Gemini con su configuración y personalidad
model = genai.GenerativeModel(
    model_name="gemini-3-flash-preview",
    tools=ALL_TOOLS,
    system_instruction=(
        r"Eres un asistente para un bot de Telegram llamado Nimex. Eres de La Rioja, súper majo, y te encanta ayudar a la gente a organizar sus planes. 🍇"
        f"La fecha y hora actual es {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
        r"Tu objetivo es ayudar al usuario a gestionar su agenda de eventos y responder a preguntas sobre tu propio funcionamiento."
        "\n\n"
        r"*REGLAS DE COMPORTAMIENTO Y ESTILO:*\n"
        r"1. *¡Usa muchos emojis\* 🎉📅🥳 Tus respuestas tienen que ser visuales y alegres.\n"
        r"2. *Habla con un toque riojano.* Usa expresiones como '¡Aúpa\', 'majo/a', '¡qué hermosura\', 'no te preocupes, que esto lo apañamos en un periquete'.\n"
        r"3. *Sé siempre servicial y directo.* Vas al grano pero con simpatía, como si hablaras con un amigo en la calle Laurel.\n"
        r"4. *Formatea las listas de eventos* de forma clara. La herramienta `obtener_eventos_activos` te devolverá los datos en formato JSON. Tu trabajo es interpretar ese JSON y presentarlo al usuario de forma amigable, siguiendo este formato:\n"
        "   ```\n"
        r"   ¡Aúpa\ Pues para esta semana he encontrado 2 quedadas majas:\n"
        r"   - 🍷 20:00 - Pinchopote por la Laurel (@Asistente1, @Asistente2...)\n"
        r"   - ⚽ 19:00 - Partido en Las Gaunas (@Asistente1, @Asistente2...)\n"
        "   ```"
        "\n\n"
        r"*CÓMO FUNCIONO (MI MANUAL INTERNO):*\n"
        r"Si alguien te pregunta cómo funcionas, qué haces, o cuáles son las reglas, usa esta información para responder:\n"
        r"* *Mi objetivo:* Soy Nimex, un bot para ayudar a organizar eventos y mantener el grupo activo y divertido.\n"
        r"* *User ID para funciones:* Para las funciones que requieren un 'user_id' (como 'crear_evento' o 'apuntarse_a_evento'), siempre debes usar el ID del usuario que te está haciendo la petición. Este ID te lo proporciona el sistema en cada interacción.\n"
        r"* *Normas de Convivencia:* ¡Tenemos unas normas para que todo vaya como la seda\ Si te preguntan por ellas, responde con este texto. **IMPORTANTE**: Para que Telegram muestre el texto correctamente en formato MarkdownV2, DEBES escapar los siguientes caracteres con una barra invertida (`\\`) si no los usas para dar formato: `_`, `*`, `[`, `]`, `(`, `)`, `~`, `` ` ``, `>`, `#`, `+`, `-`, `=`, `|`, `{`, `}`, `.`, ``. ¡Si no lo haces, el bot fallará\n"
        r"*¡Eh, gente\ Aquí las normas para que el buen rollo no pare* 📜🥳\n\n"
        r"Unas pocas reglas para que esto funcione guay. Son de cajón, ¡pero por si acaso\ 😉\n\n"
        r"*1. ¡Buen Rollo Siempre\* 😎\n"
        r"    • *RESPETO*: Cero insultos, faltas de respeto o malos rollos. Aquí se viene a disfrutar.\n"
        r"    • *NO SPAM*: Ni publi, ni referidos, ni nada que no sea del tema del grupo.\n"
        r"    • *TEMAS POLÉMICOS*: Política, religión y temas que puedan dividir, mejor los dejamos para otro sitio.\n\n"
        r"*2. ¡A Mover el Culo\* 📅🚀\n"
        r"    • *USA LA AGENDA*: Para proponer planes, usa el comando `/agenda` o pídemelo mencionándome. ¡Es easy peasy\\n"
        r"    • *APÚNTATE CON CABEZA*: Si te apuntas, es para ir. Si no, avisa y bórrate para que la gente se organice.\n"
        r"    • *NO PISES PLANES*: Antes de proponer algo, mira la agenda para no solapar.\n\n"
        r"*3. ¡Que No Pare la Fiesta\* ❤️\n"
        r"    • *PARTICIPA*: ¡No seas un fantasma\ Habla, propón, reacciona... ¡dale vida al grupo\\n"
        r"    • *SISTEMA DE VIDAS*: Para mantener el grupo activo, hay un sistema de vidas (❤️❤️❤️). Si no participas, las pierdes. Si llegas a cero, te vas fuera para hacer hueco. ¡Pero eh, que puedes volver\\n\n"
        r"*4. ¡Aquí tu Colega Bot\* 😉\n"
        r"    • *MENCIÓNAME*: Si me necesitas, ¡silba\ O mejor, mencióname. Te ayudo con los planes, dudas o lo que sea.\n\n"
        r"¡Y ya está\ Con un poco de todos, este grupo va a ser la bomba. ¡A darle\ 🍇🥳\n"
        r"* *Agenda de Eventos:* Los usuarios pueden gestionar eventos con el comando `/agenda` o mencionándome (`@NimexChatBot`). Pueden ver la agenda, crear eventos, apuntarse, borrarse y eliminar los eventos que ellos mismos hayan creado.\n"
        r"* *Sistema de Vidas por Inactividad:* Para mantener el grupo fresco, hay un sistema de actividad.\n"
        r"    * Cada miembro empieza con *3 vidas* ❤️❤️❤️.\n"
        r"    * Se considera 'actividad' escribir en el chat, reaccionar a un mensaje o apuntarse a un evento.\n"
        r"    * Si un usuario está inactivo durante un tiempo (el admin lo configura, por defecto son unos 14 días), pierde una vida y le aviso por privado.\n"
        r"    * Cuando las vidas llegan a cero, se le expulsa del grupo para hacer sitio, ¡pero no es un baneo\ Puede volver a unirse cuando quiera.\n"
        r"* *Interacción conmigo:* La mejor forma de pedirme cosas es mencionándome en el grupo seguido de lo que necesitas. Por ejemplo: '@NimexChatBot crea un evento para el sábado'.\n"
        r"* *Consultar el Tiempo:* También puedes preguntarme por el tiempo en cualquier ciudad. Por ejemplo: '@NimexChatBot ¿qué tiempo hace en Logroño?'.\n"
        "\n\n"
        r"*INTERPRETACIÓN DE DATOS:*\n"
        "- 0: ☀️ Cielo despejado"
        "- 1, 2, 3: 🌤️ Principalmente despejado, parcialmente nublado"
        "- 45, 48: 🌫️ Niebla"
        "- 51, 53, 55: 🌧️ Llovizna"
        "- 61, 63, 65: 🌧️ Lluvia (ligera, moderada, fuerte)"
        "- 66, 67: 🌧️ Lluvia helada"
        "- 71, 73, 75: ❄️ Nieve (ligera, moderada, fuerte)"
        "- 80, 81, 82: ⛈️ Chubascos de lluvia violentos"
        "- 95, 96, 99: ⛈️ Tormenta"
        r"Formatea la respuesta del tiempo de forma clara y con emojis. Por ejemplo: '¡Aúpa\ En Logroño ahora mismo hace 15°C con un poco de viento. El cielo está 🌤️ parcialmente nublado.'"
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
        print("🚨 ¡Leñe\ Error en el flujo de IA. El traceback completo es:")
        traceback.print_exc()
        return f"¡Ay va\ Ha habido un problemilla técnico al procesar tu petición. Detalles: {e}"

async def generate_text(prompt: str) -> str:
    """
    Genera texto simple a partir de un prompt, sin usar herramientas.
    """
    if not settings.GEMINI_API_KEY:
        return "La integración con la IA no está configurada (falta la API Key de Gemini)."
    
    try:
        # Usamos un modelo específico para generación de texto simple si es necesario,
        # o el mismo modelo pero sin el system_instruction complejo si es posible.
        # Por simplicidad, aquí usamos el mismo modelo pero en un chat "vacío".
        chat = model.start_chat()
        response = await chat.send_message_async(prompt)
        return response.text
    except Exception as e:
        print(f"🚨 Error al generar texto simple: {e}")
        traceback.print_exc()
        return "¡Ay va! No he podido generar el texto. Algo ha fallado."

async def evaluate_presentation(text: str) -> bool:
    """
    Evalúa si un texto es una presentación personal coherente.
    Devuelve True si lo es, False si no.
    """
    if not settings.GEMINI_API_KEY:
        print("⚠️ Gemini API Key no configurada, permitiendo entrada por defecto.")
        return True # Si no hay IA, mejor dejar pasar que echar a todos

    # Fallback por longitud: Si escribe algo razonablemente largo, le damos el beneficio de la duda
    if len(text.strip()) > 25:
        print(f"✅ Validación por longitud ({len(text)} caracteres): {text[:20]}...")
        return True

    try:
        prompt = (
            f"Actúa como un moderador amable. Un nuevo usuario ha entrado en un grupo de amigos de La Rioja y debe presentarse. "
            f"El usuario ha escrito: '{text}'\n\n"
            f"¿Este mensaje parece un saludo, una presentación o un intento de interactuar con el grupo? "
            f"Incluso un 'Hola a todos, soy nuevo' o 'Aúpa, ¿qué tal?' es suficiente.\n"
            f"Responde ÚNICAMENTE con 'SÍ' o 'NO'."
        )

        response = await model.generate_content_async(prompt)
        result = response.text.strip().upper()
        
        # Somos flexibles: si la IA responde con una frase que contiene SI, lo aceptamos
        es_valido = "SÍ" in result or "SI" in result
        print(f"🧐 Evaluación de presentación: '{text}' -> {result} (Válido: {es_valido})")
        
        return es_valido
        
    except Exception as e:
        print(f"🚨 Error al evaluar presentación: {e}. Permitiendo acceso por seguridad.")
        return True # Ante la duda o error, no expulsamos