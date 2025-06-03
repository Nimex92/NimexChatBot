from openai import OpenAI
import json
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from collections import defaultdict
from datetime import datetime, timedelta

# 🔐 Claves
TELEGRAM_TOKEN = '7554884887:AAGS890omOq3rf4Q2y1nHkrI9N6SnCjRk7U'
OPENAI_API_KEY = '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'
OpenAI.api_key = OPENAI_API_KEY
# Crea el cliente con tu API key (o configúralo en la variable de entorno OPENAI_API_KEY)
client = OpenAI(api_key="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")

# 🧠 Historial de GPT por usuario
historial_usuarios = {}
MAX_HISTORIAL = 10

# 📅 Agenda semanal
agenda = defaultdict(list)

# 🧩 Estados de usuario para introducir evento
estado_usuario = {}       # user_id → estado del flujo
datos_temporales = {}     # user_id → datos intermedios


AGENDA_FILE = "agenda.json"

def guardar_agenda():
    with open(AGENDA_FILE, "w", encoding="utf-8") as f:
        json.dump(agenda, f, indent=2, ensure_ascii=False)

def cargar_agenda():
    if os.path.exists(AGENDA_FILE):
        with open(AGENDA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Convertir a defaultdict(list)
            for fecha, eventos in data.items():
                agenda[fecha] = eventos
# 🟢 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    historial_usuarios[user_id] = []
    await update.message.reply_text("👋 ¡Hola! Soy tu asistente 🤖 con memoria 🧠 y agenda 📅 integrada. \n✍️ Escríbeme lo que necesites o usa /agenda 📌 para: \n🔍 Consultar eventos \n➕ Registrar nuevos \n✅ Inscribirte con un clic \n\n\n📲 ¡Organízate fácil y rápido, estés donde estés!")

# 🔁 /reset (borra historial GPT)
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    historial_usuarios[user_id] = []
    await update.message.reply_text("🧠 Memoria borrada. Empecemos de nuevo.")

# 📌 /agenda (muestra botones)
async def agenda_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📅 Ver agenda", callback_data='ver_agenda'),
            InlineKeyboardButton("✍️ Introducir evento", callback_data='introducir_evento'),
        ],
        [
            InlineKeyboardButton("✅ Inscribirme a evento", callback_data='inscribirme_evento'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("¿Qué quieres hacer con la agenda?", reply_markup=reply_markup)

# 🔘 Maneja botones del menú
async def handle_agenda_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    if action == "ver_agenda":
        await mostrar_agenda(update, context)
    elif action == "introducir_evento":
        await introducir_evento(update, context)
    elif action == "inscribirme_evento":
        await inscribirme_evento(update, context)
    else:
        await query.edit_message_text("Acción no reconocida.")

def formatear_nombre(asistente):
    if isinstance(asistente, dict):
        return f"@{asistente['username']}" if "username" in asistente else asistente.get("nombre", "Desconocido")
    return "Desconocido"

# 📅 Mostrar agenda de las próximas 2 semanas
async def mostrar_agenda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hoy = datetime.today()
    mensaje = "📅 *Agenda (próximas 2 semanas)*\n\n"
    for i in range(14):
        fecha = hoy + timedelta(days=i)
        clave_fecha = fecha.strftime("%Y-%m-%d")
        eventos = agenda.get(clave_fecha, [])

        if eventos:
            mensaje += f"*{fecha.strftime('%A %d %b')}*\n"
            for e in eventos:
                asistentes = ', '.join([formatear_nombre(a) for a in e["asistentes"]])
                mensaje += (
                    f"🕑 {e['hora']} - {e['titulo']} \n"
                    f"👥 Asistentes: {asistentes or 'Nadie aún'}\n"
                )
            mensaje += "\n"
    if mensaje.strip() == "📅 *Agenda (próximas 2 semanas)*":
        mensaje += "_No hay eventos programados._"

    await update.callback_query.edit_message_text(mensaje, parse_mode="Markdown")

# 📝 Iniciar flujo para introducir evento
async def introducir_evento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    estado_usuario[user_id] = "esperando_fecha"
    datos_temporales[user_id] = {}
    await update.callback_query.edit_message_text("📅 Escribe la *fecha* del evento en formato `YYYY-MM-DD`:", parse_mode="Markdown")

# ✉️ Maneja mensajes: flujo evento o GPT
async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text.strip()
    estado = estado_usuario.get(user_id)

    # Flujo paso a paso
    if estado == "esperando_fecha":
        try:
            datetime.strptime(texto, "%Y-%m-%d")
            datos_temporales[user_id]["fecha"] = texto
            estado_usuario[user_id] = "esperando_hora"
            await update.message.reply_text("🕒 Escribe la *hora* del evento en formato `HH:MM`:", parse_mode="Markdown")
        except:
            await update.message.reply_text("❌ Formato inválido. Usa `YYYY-MM-DD`.")

    elif estado == "esperando_hora":
        try:
            datetime.strptime(texto, "%H:%M")
            datos_temporales[user_id]["hora"] = texto
            estado_usuario[user_id] = "esperando_titulo"
            await update.message.reply_text("📝 Escribe el *título* del evento:", parse_mode="Markdown")
        except:
            await update.message.reply_text("❌ Formato inválido. Usa `HH:MM`.")

    elif estado == "esperando_titulo":
        datos_temporales[user_id]["titulo"] = texto
        evento = {
            "hora": datos_temporales[user_id]["hora"],
            "titulo": datos_temporales[user_id]["titulo"],
            "asistentes": []
        }
        fecha = datos_temporales[user_id]["fecha"]
        agenda[fecha].append(evento)
        guardar_agenda()

        # Limpieza
        estado_usuario[user_id] = None
        datos_temporales[user_id] = {}

        await update.message.reply_text("✅ Evento guardado con éxito.")

    # else:
        # await chat(update, context)

# 💬 Chat con GPT
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    await update.message.chat.send_action(action="typing")

    if user_id not in historial_usuarios:
        historial_usuarios[user_id] = []

    historial_usuarios[user_id].append({"role": "user", "content": user_message})
    historial_reciente = historial_usuarios[user_id][-MAX_HISTORIAL:]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_message}] + historial_reciente,
            max_tokens=300,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()
        historial_usuarios[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"Error al responder: {str(e)}")


async def inscribirme_evento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    hoy = datetime.today()
    mensaje = "✅ *Elige un evento para inscribirte:*\n"
    keyboard = []

    for i in range(14):
        fecha = hoy + timedelta(days=i)
        clave_fecha = fecha.strftime("%Y-%m-%d")
        eventos = agenda.get(clave_fecha, [])

        if eventos:
            # Añade encabezado de fecha
            mensaje += f"\n📅 *{fecha.strftime('%A %d %b')}*\n"
            for idx, evento in enumerate(eventos):
                texto_boton = f"🕑 {evento['hora']} - {evento['titulo']}"
                data = f"inscribirse|{clave_fecha}|{idx}"
                keyboard.append([InlineKeyboardButton(texto_boton, callback_data=data)])

    if not keyboard:
        await update.callback_query.edit_message_text("😕 No hay eventos disponibles aún.")
    else:
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(mensaje, parse_mode="Markdown", reply_markup=reply_markup)


async def manejar_inscripcion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    nombre = user.first_name
    username = user.username

    try:
        _, fecha, idx = query.data.split("|")
        idx = int(idx)
    except ValueError:
        await query.answer("❌ Datos inválidos.")
        return

    if fecha not in agenda or idx >= len(agenda[fecha]):
        await query.answer("❌ Evento no encontrado.")
        return

    evento = agenda[fecha][idx]

    # Evitar duplicados
    ya_inscrito = any(a["id"] == user_id for a in evento["asistentes"])
    if ya_inscrito:
        await query.answer("Ya estás inscrito en este evento.")
        return

    asistente = {
        "id": user_id,
        "nombre": nombre
    }
    if username:
        asistente["username"] = username

    evento["asistentes"].append(asistente)
    guardar_agenda()

    await query.answer("✅ Inscripción confirmada.")
    await query.edit_message_text(
        f"✅ Te has inscrito al evento:\n\n"
        f"📅 *{fecha}*\n"
        f"🕒 *{evento['hora']}*\n"
        f"📌 *{evento['titulo']}*",
        parse_mode="Markdown"
    )


# 🚀 Inicia el bot
if __name__ == "__main__":
    cargar_agenda()  # Cargar agenda al iniciar
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("agenda", agenda_menu))
    app.add_handler(CallbackQueryHandler(manejar_inscripcion, pattern=r"^inscribirse\|"))
    app.add_handler(CallbackQueryHandler(handle_agenda_callback))
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    print("✅ Bot en marcha con historial y agenda...")
    app.run_polling()
# Fin del código