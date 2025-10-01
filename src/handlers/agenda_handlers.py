# src/handlers/agenda_handlers.py
"""Manejadores de eventos relacionados con la agenda.

Este módulo contiene toda la lógica para interactuar con el usuario a través
de menús de botones (InlineKeyboards) y conversaciones de varios pasos para
gestionar la agenda. Incluye funciones para:
- Mostrar el menú principal de la agenda.
- Visualizar los eventos programados.
- Crear nuevos eventos paso a paso (fecha, hora, nombre).
- Inscribirse, darse de baja y eliminar eventos.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from babel.dates import format_datetime
import locale

from src.managers import agenda_manager

locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

async def main_agenda_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Punto de entrada para todos los callbacks de la agenda.

    Esta función actúa como un enrutador. Lee el `callback_data`, que sigue
    el formato "accion|param1|param2|...", y llama a la función
    correspondiente basándose en la `accion`.

    Args:
        update (Update): El objeto de actualización de Telegram.
        context (ContextTypes.DEFAULT_TYPE): El contexto del bot.
    """
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('|')
    action = parts[0]

    # Enrutamiento de acciones
    action_router = {
        'ver_agenda': mostrar_agenda,
        'inscribir_menu': inscribirme_menu,
        'desinscribir_menu': darse_baja_menu,
        'eliminar_menu': eliminar_evento_menu,
        'crear_evento_fecha': pedir_fecha_creacion,
        'fecha_seleccionada': lambda q, c: guardar_fecha_y_pedir_hora(q, c, fecha=parts[1]),
        'hora_seleccionada': lambda q, c: guardar_hora_y_pedir_nombre(q, c, hora=parts[1]),
        'inscribirse': lambda q, c: manejar_inscripcion(q, fecha=parts[1], idx=int(parts[2])),
        'desinscribirse': lambda q, c: manejar_desinscripcion(q, fecha=parts[1], idx=int(parts[2])),
        'eliminar': lambda q, c: manejar_eliminacion(q, fecha=parts[1], idx=int(parts[2])),
    }

    if action in action_router:
        # Algunas funciones necesitan el contexto, otras no.
        if action in ['crear_evento_fecha', 'fecha_seleccionada', 'hora_seleccionada']:
            await action_router[action](query, context)
        else:
            await action_router[action](query)


async def agenda_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú principal de la agenda con botones de acción.

    Args:
        update (Update): El objeto de actualización de Telegram.
        context (ContextTypes.DEFAULT_TYPE): El contexto del bot.
    """
    keyboard = [
        [InlineKeyboardButton("📅 Ver agenda", callback_data='ver_agenda')],
        [InlineKeyboardButton("✍️ Crear un evento", callback_data='crear_evento_fecha')],
        [InlineKeyboardButton("✅ Inscribirme a un evento", callback_data='inscribir_menu')],
        [InlineKeyboardButton("❌ Darme de baja", callback_data='desinscribir_menu')],
        [InlineKeyboardButton("🗑️ Eliminar evento creado", callback_data='eliminar_menu')]
    ]
    await update.message.reply_text("¿Qué quieres hacer con la agenda?", reply_markup=InlineKeyboardMarkup(keyboard))

async def mostrar_agenda(query: CallbackQuery):
    """Formatea y muestra los eventos activos de las próximas 2 semanas.

    Args:
        query (CallbackQuery): El objeto de callback query de la interacción.
    """
    eventos_data = agenda_manager.obtener_eventos_activos()
    mensaje = "📅 *Agenda de Próximos Eventos*\n\n"
    if not eventos_data:
        mensaje += "_No hay nada programado._"
    else:
        for item in eventos_data:
            fecha_dt = datetime.strptime(item['fecha'], "%Y-%m-%d")
            nombre_dia = format_datetime(fecha_dt, "EEEE, d 'de' MMMM", locale="es").capitalize()
            mensaje += f"*{nombre_dia}*\n"
            for _, evento in item['eventos']:
                asistentes = ', '.join([a.get('nombre', 'Anónimo') for a in evento["asistentes"]])
                mensaje += f"  🕑 `{evento['hora']}` - {evento['titulo']}\n"
                if asistentes:
                    mensaje += f"  👥 _{asistentes}_\n"
            mensaje += "\n"
    await query.edit_message_text(mensaje, parse_mode="Markdown")

async def pedir_fecha_creacion(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Muestra un teclado con los próximos 14 días para crear un evento.

    Args:
        query (CallbackQuery): El objeto de callback query.
        context (ContextTypes.DEFAULT_TYPE): El contexto del bot.
    """
    botones = []
    hoy = datetime.today()
    for i in range(14):
        fecha = hoy + timedelta(days=i)
        texto = format_datetime(fecha, "EEE d MMM", locale="es").capitalize()
        callback_data = f"fecha_seleccionada|{fecha.strftime('%Y-%m-%d')}"
        botones.append(InlineKeyboardButton(texto, callback_data=callback_data))
    
    keyboard = [botones[i:i+3] for i in range(0, len(botones), 3)]
    await query.edit_message_text("PASO 1: Elige la fecha del evento.", reply_markup=InlineKeyboardMarkup(keyboard))

async def guardar_fecha_y_pedir_hora(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, fecha: str):
    """Guarda la fecha seleccionada en `user_data` y pide la hora.

    Args:
        query (CallbackQuery): El objeto de callback query.
        context (ContextTypes.DEFAULT_TYPE): El contexto del bot.
        fecha (str): La fecha seleccionada en formato 'YYYY-MM-DD'.
    """
    context.user_data['nuevo_evento'] = {'fecha': fecha}

    botones = [
        InlineKeyboardButton(f"{h:02d}:{m:02d}", callback_data=f"hora_seleccionada|{h:02d}:{m:02d}")
        for h in range(8, 23) for m in (0, 30)
    ]
    keyboard = [botones[i:i+4] for i in range(0, len(botones), 4)]
    await query.edit_message_text("PASO 2: Ahora elige la hora.", reply_markup=InlineKeyboardMarkup(keyboard))

async def guardar_hora_y_pedir_nombre(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, hora: str):
    """Guarda la hora, pide el nombre del evento y cambia el estado del usuario.

    Args:
        query (CallbackQuery): El objeto de callback query.
        context (ContextTypes.DEFAULT_TYPE): El contexto del bot.
        hora (str): La hora seleccionada en formato 'HH:MM'.
    """
    context.user_data['nuevo_evento']['hora'] = hora
    context.user_data['estado'] = 'esperando_nombre_evento'
    
    fecha_dt = datetime.strptime(context.user_data['nuevo_evento']['fecha'], "%Y-%m-%d")
    fecha_texto = format_datetime(fecha_dt, "EEEE d", locale="es")
    
    await query.edit_message_text(f"Perfecto. Evento para el *{fecha_texto} a las {hora}*.\n\n"
                                  "PASO 3: Ahora, dime en un mensaje el nombre o título del evento.",
                                  parse_mode="Markdown")

async def inscribirme_menu(query: CallbackQuery):
    """Muestra un menú con los eventos disponibles para inscribirse.

    Args:
        query (CallbackQuery): El objeto de callback query.
    """
    eventos_data = agenda_manager.obtener_eventos_activos()
    keyboard = []
    for item in eventos_data:
        for idx, evento in item['eventos']:
            fecha_corta = datetime.strptime(item['fecha'], '%Y-%m-%d').strftime('%d/%m')
            texto = f"({fecha_corta}) {evento['hora']} - {evento['titulo']}"
            callback_data = f"inscribirse|{item['fecha']}|{idx}"
            keyboard.append([InlineKeyboardButton(texto, callback_data=callback_data)])
    
    if not keyboard:
        await query.edit_message_text("ℹ️ No hay eventos disponibles para inscribirse ahora mismo.")
        return
    await query.edit_message_text("Elige un evento para apuntarte:", reply_markup=InlineKeyboardMarkup(keyboard))

async def darse_baja_menu(query: CallbackQuery):
    """Muestra al usuario los eventos en los que está inscrito para darse de baja.

    Args:
        query (CallbackQuery): El objeto de callback query.
    """
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

async def eliminar_evento_menu(query: CallbackQuery):
    """Muestra al creador los eventos que puede eliminar.

    Args:
        query (CallbackQuery): El objeto de callback query.
    """
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

async def manejar_inscripcion(query: CallbackQuery, fecha: str, idx: int):
    """Procesa la inscripción de un usuario a un evento.

    Args:
        query (CallbackQuery): El objeto de callback query.
        fecha (str): La fecha del evento.
        idx (int): El índice del evento.
    """
    user = query.from_user
    user_info = {"id": user.id, "nombre": user.first_name, "username": user.username}
    
    if agenda_manager.inscribir_usuario(fecha, idx, user_info):
        await query.edit_message_text("✅ ¡Genial! Te has inscrito correctamente.")
    else:
        await query.edit_message_text("⚠️ Ya estabas inscrito en este evento.")

async def manejar_desinscripcion(query: CallbackQuery, fecha: str, idx: int):
    """Procesa la baja de un usuario de un evento.

    Args:
        query (CallbackQuery): El objeto de callback query.
        fecha (str): La fecha del evento.
        idx (int): El índice del evento.
    """
    user_id = query.from_user.id
    if agenda_manager.desinscribir_usuario(fecha, idx, user_id):
        await query.edit_message_text("👍 Te has borrado del evento.")
    else:
        await query.edit_message_text("🤔 Parece que no estabas en la lista.")

async def manejar_eliminacion(query: CallbackQuery, fecha: str, idx: int):
    """Procesa la eliminación (desactivación) de un evento.

    Args:
        query (CallbackQuery): El objeto de callback query.
        fecha (str): La fecha del evento.
        idx (int): El índice del evento.
    """
    evento = agenda_manager.desactivar_evento(fecha, idx)
    if evento:
        await query.edit_message_text(f"🗑️ El evento '{evento['titulo']}' ha sido eliminado (desactivado).")
    else:
        await query.edit_message_text("❌ No se pudo encontrar el evento para eliminar.")


async def manejar_mensajes_de_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los mensajes de texto que no son comandos.

    Comprueba si el usuario está en medio de la creación de un evento
    (estado 'esperando_nombre_evento'). Si es así, utiliza el texto del
    mensaje como título del evento y finaliza el proceso de creación.

    Si el usuario no está en ese estado, se envía un mensaje de ayuda
    para guiarle sobre cómo usar los comandos.

    Args:
        update (Update): El objeto de actualización de Telegram.
        context (ContextTypes.DEFAULT_TYPE): El contexto del bot.
    """
    user_id = update.effective_user.id
    estado = context.user_data.get('estado')

    if estado == 'esperando_nombre_evento':
        titulo_evento = update.message.text
        datos_evento = context.user_data.get('nuevo_evento', {})
        
        agenda_manager.crear_evento(
            fecha=datos_evento['fecha'],
            hora=datos_evento['hora'],
            titulo=titulo_evento,
            creador_id=user_id
        )
        
        await update.message.reply_text("✅ ¡Evento guardado con éxito!")
        
        # Limpiar el estado para futuras interacciones
        context.user_data.pop('estado', None)
        context.user_data.pop('nuevo_evento', None)
    else:
        # Si no se está esperando una respuesta, se envía un mensaje de ayuda.
        await update.message.reply_text(
            "No he entendido eso. 🤔\n"
            "Para interactuar con la agenda, usa el comando /agenda.\n"
            "Para hablar con la IA, usa /ia."
        )