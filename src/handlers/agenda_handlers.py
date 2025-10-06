# src/handlers/agenda_handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from babel.dates import format_datetime
from telegram.helpers import escape_markdown
import locale

# Para los nombres de los días/meses en español
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

# Importamos el manager, que es el único que habla con la agenda
from src.managers import agenda_manager
# Importamos el handler del chat para derivar los mensajes que no son de la agenda
from src.handlers import general_handlers

# --- MANEJADOR PRINCIPAL DE CALLBACKS ---

async def main_agenda_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Una única función que recibe todos los callbacks y los distribuye.
    """
    query = update.callback_query
    await query.answer()
    
    # Formato del callback: "accion|param1|param2|..."
    parts = query.data.split('|')
    action = parts[0]

    # Menús principales
    if action == 'ver_agenda':
        await mostrar_agenda(query)
    elif action == 'inscribir_menu':
        await inscribirme_menu(query)
    elif action == 'desinscribir_menu':
        await darse_baja_menu(query)
    elif action == 'eliminar_menu':
        await eliminar_evento_menu(query)

    # Flujo de creación de eventos
    elif action == 'crear_evento_fecha':
        await pedir_fecha_creacion(query, context)
    elif action == 'fecha_seleccionada':
        await guardar_fecha_y_pedir_hora(query, context, fecha=parts[1])
    elif action == 'hora_seleccionada':
        await guardar_hora_y_pedir_nombre(query, context, hora=parts[1])

    # Acciones finales
    elif action == 'inscribirse':
        await manejar_inscripcion(query, fecha=parts[1], idx=int(parts[2]))
    elif action == 'desinscribirse':
        await manejar_desinscripcion(query, fecha=parts[1], idx=int(parts[2]))
    elif action == 'eliminar':
        await manejar_eliminacion(query, fecha=parts[1], idx=int(parts[2]))

# --- Menú y Vistas ---

async def agenda_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú principal de la agenda."""
    keyboard = [
        [InlineKeyboardButton("📅 Ver agenda", callback_data='ver_agenda')],
        [InlineKeyboardButton("✍️ Crear un evento", callback_data='crear_evento_fecha')],
        [InlineKeyboardButton("✅ Inscribirme a un evento", callback_data='inscribir_menu')],
        [InlineKeyboardButton("❌ Darme de baja", callback_data='desinscribir_menu')],
        [InlineKeyboardButton("🗑️ Eliminar evento creado", callback_data='eliminar_menu')]
    ]
    await update.message.reply_text("¿Qué quieres hacer con la agenda?", reply_markup=InlineKeyboardMarkup(keyboard))

async def mostrar_agenda(query: Update.callback_query):
    """Muestra los eventos activos de las próximas 2 semanas."""
    eventos_por_fecha = agenda_manager.obtener_eventos_activos()
    mensaje = "📅 *Agenda de Próximos Eventos*\n\n"
    
    if not eventos_por_fecha:
        mensaje += "_No hay nada programado_\."
    else:
        for fecha_str, eventos in eventos_por_fecha.items():
            fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d")
            nombre_dia = format_datetime(fecha_dt, "EEEE, d 'de' MMMM", locale="es").capitalize()
            mensaje += f"*{nombre_dia}*\n"
            
            for evento in eventos:
                # --- AQUÍ ESTÁ LA MAGIA ---
                # Escapamos cualquier carácter especial en el título y los asistentes
                titulo = escape_markdown(str(evento.get('titulo', 'Evento sin título')), version=2)
                hora = escape_markdown(str(evento.get('hora', 'Sin hora')), version=2)
                
                asistentes_lista = [escape_markdown(str(a.get('nombre', 'Anónimo')), version=2) for a in evento.get("asistentes", [])]
                asistentes = ', '.join(asistentes_lista)
                # -------------------------
                
                # Usamos las variables "limpias" y seguras
                mensaje += f"  🕑 `{hora}` \- {titulo}\n"
                if asistentes:
                    mensaje += f"  👥 _{asistentes}_\n"
            mensaje += "\n"
            
    await query.edit_message_text(mensaje, parse_mode="MarkdownV2")

# --- Flujo de Creación de Eventos ---

async def pedir_fecha_creacion(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE):
    """Muestra botones para seleccionar una fecha."""
    botones = []
    hoy = datetime.today()
    for i in range(14):
        fecha = hoy + timedelta(days=i)
        texto = format_datetime(fecha, "EEE d MMM", locale="es").capitalize()
        callback_data = f"fecha_seleccionada|{fecha.strftime('%Y-%m-%d')}"
        botones.append(InlineKeyboardButton(texto, callback_data=callback_data))
    
    keyboard = [botones[i:i+3] for i in range(0, len(botones), 3)] # Filas de 3
    await query.edit_message_text("PASO 1: Elige la fecha del evento.", reply_markup=InlineKeyboardMarkup(keyboard))

async def guardar_fecha_y_pedir_hora(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE, fecha: str):
    """Guarda la fecha y muestra botones para la hora."""
    context.user_data['nuevo_evento'] = {'fecha': fecha} # Guardamos en el contexto del usuario
    
    botones = []
    for h in range(8, 23): # Horas razonables
        for m in (0, 30):
            hora_str = f"{h:02d}:{m:02d}"
            callback_data = f"hora_seleccionada|{hora_str}"
            botones.append(InlineKeyboardButton(hora_str, callback_data=callback_data))

    keyboard = [botones[i:i+4] for i in range(0, len(botones), 4)] # Filas de 4
    await query.edit_message_text("PASO 2: Ahora elige la hora.", reply_markup=InlineKeyboardMarkup(keyboard))

async def guardar_hora_y_pedir_nombre(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE, hora: str):
    """Guarda la hora, pide el nombre y actualiza el estado."""
    context.user_data['nuevo_evento']['hora'] = hora
    context.user_data['estado'] = 'esperando_nombre_evento' # ¡Importante!
    
    fecha_dt = datetime.strptime(context.user_data['nuevo_evento']['fecha'], "%Y-%m-%d")
    fecha_texto = format_datetime(fecha_dt, "EEEE d", locale="es")
    
    await query.edit_message_text(f"Perfecto\. Evento para el *{fecha_texto} a las {hora}*\.\n\n"
                                  "PASO 3: Ahora, dime en un mensaje el nombre o título del evento\.",
                                  parse_mode="MarkdownV2")

# --- Flujos de Inscripción, Baja y Eliminación ---

async def inscribirme_menu(query: Update.callback_query):
    """Muestra los eventos a los que un usuario se puede inscribir."""
    eventos_por_fecha = agenda_manager.obtener_eventos_activos()
    keyboard = []
    
    for fecha_str, eventos in eventos_por_fecha.items():
        for idx, evento in enumerate(eventos):
            # --- HEMOS ELIMINADO EL FILTRO 'if' QUE ESTABA AQUÍ ---
            # Ahora todos los eventos aparecen en la lista, incluso los creados por ti.
            fecha_corta = datetime.strptime(fecha_str, '%Y-%m-%d').strftime('%d/%m')
            texto = f"({fecha_corta}) {evento['hora']} - {evento['titulo']}"
            callback_data = f"inscribirse|{fecha_str}|{idx}"
            keyboard.append([InlineKeyboardButton(texto, callback_data=callback_data)])
    
    if not keyboard:
        await query.edit_message_text("ℹ️ ¡Aúpa! Parece que no hay eventos disponibles para apuntarse ahora mismo.")
        return
        
    await query.edit_message_text("¡Majo! Elige un evento para apuntarte:", reply_markup=InlineKeyboardMarkup(keyboard))



async def darse_baja_menu(query: Update.callback_query):
    """Muestra al usuario los eventos en los que está inscrito para darse de baja."""
    user_id = query.from_user.id
    eventos_inscrito = agenda_manager.obtener_eventos_inscrito(user_id)
    keyboard = []
    for item in eventos_inscrito:
        evento = item['evento']
        fecha_corta = datetime.strptime(item['fecha'], '%Y-%m-%d').strftime('%d/%m')
        texto = f"({fecha_corta}) {evento['hora']} - {evento['titulo']}"
        callback_data = f"desinscribirse|{item['fecha']}|{item['idx']}"
        keyboard.append([InlineKeyboardButton(texto, callback_data=callback_data)])

    if not keyboard:
        await query.edit_message_text("ℹ️ No estás inscrito en ningún evento próximo.")
        return
    await query.edit_message_text("Elige de qué evento quieres borrarte:", reply_markup=InlineKeyboardMarkup(keyboard))

async def eliminar_evento_menu(query: Update.callback_query):
    """Muestra al creador los eventos que puede eliminar."""
    user_id = query.from_user.id
    eventos_creados = agenda_manager.obtener_eventos_creados_por(user_id)
    keyboard = []
    for item in eventos_creados:
        evento = item['evento']
        fecha_corta = datetime.strptime(item['fecha'], '%Y-%m-%d').strftime('%d/%m')
        texto = f"({fecha_corta}) {evento['hora']} - {evento['titulo']}"
        callback_data = f"eliminar|{item['fecha']}|{item['idx']}"
        keyboard.append([InlineKeyboardButton(texto, callback_data=callback_data)])
    
    if not keyboard:
        await query.edit_message_text("ℹ️ No tienes ningún evento activo que hayas creado tú.")
        return
    await query.edit_message_text("Elige qué evento quieres eliminar (se marcará como inactivo):", reply_markup=InlineKeyboardMarkup(keyboard))

# --- Lógica de Acciones ---

async def manejar_inscripcion(query: Update.callback_query, fecha: str, idx: int):
    user = query.from_user
    user_info = {"id": user.id, "nombre": user.first_name, "username": user.username}
    
    if agenda_manager.inscribir_usuario(fecha, idx, user_info):
        await query.edit_message_text("✅ ¡Genial! Te has inscrito correctamente.")
    else:
        await query.edit_message_text("⚠️ Ya estabas inscrito en este evento.")

async def manejar_desinscripcion(query: Update.callback_query, fecha: str, idx: int):
    user_id = query.from_user.id
    if agenda_manager.desinscribir_usuario(fecha, idx, user_id):
        await query.edit_message_text("👍 Te has borrado del evento.")
    else:
        await query.edit_message_text("🤔 Parece que no estabas en la lista.")

async def manejar_eliminacion(query: Update.callback_query, fecha: str, idx: int):
    evento = agenda_manager.desactivar_evento(fecha, idx)
    if evento:
        await query.edit_message_text(f"🗑️ El evento '{evento['titulo']}' ha sido eliminado (desactivado).")
    else:
        await query.edit_message_text("❌ No se pudo encontrar el evento para eliminar.")

# --- Manejador de Mensajes de Texto ---

# ... (todo el código anterior de agenda_handlers.py se mantiene igual) ...

# --- Manejador de Mensajes de Texto ---

async def manejar_mensajes_de_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Revisa el estado del usuario. Si está creando un evento, procesa el texto.
    Si no, le indica al usuario cómo interactuar.
    """
    user_id = update.effective_user.id
    estado = context.user_data.get('estado')

    if estado == 'esperando_nombre_evento':
        titulo_evento = update.message.text
        datos_evento = context.user_data.get('nuevo_evento', {})
        
        # Llamamos al manager para que cree el evento
        agenda_manager.crear_evento(
            fecha=datos_evento['fecha'],
            hora=datos_evento['hora'],
            titulo=titulo_evento,
            creador_id=user_id
        )
        
        await update.message.reply_text("✅ ¡Evento guardado con éxito!")
        
        # Limpiamos el estado y los datos temporales del usuario
        context.user_data.pop('estado', None)
        context.user_data.pop('nuevo_evento', None)
    # else:
        # Si no hay un estado activo, le recordamos al usuario cómo usar el bot
        # await update.message.reply_text("No he entendido eso. 🤔\nPara ver, crear o modificar eventos, usa el comando /agenda.")
    """
    Revisa el estado del usuario. Si está creando un evento, procesa el texto.
    Si no, lo envía al chat general con la IA.
    """
    user_id = update.effective_user.id
    estado = context.user_data.get('estado')

    if estado == 'esperando_nombre_evento':
        titulo_evento = update.message.text
        datos_evento = context.user_data.get('nuevo_evento', {})
        
        # Llamamos al manager para que cree el evento
        agenda_manager.crear_evento(
            fecha=datos_evento['fecha'],
            hora=datos_evento['hora'],
            titulo=titulo_evento,
            creador_id=user_id
        )
        
        await update.message.reply_text("✅ ¡Evento guardado con éxito!")
        
        # Limpiamos el estado y los datos temporales del usuario
        context.user_data.pop('estado', None)
        context.user_data.pop('nuevo_evento', None)
    # else:
        # Si no hay un estado activo, es un mensaje normal para el chat
        # await general_handlers.chat(update, context)