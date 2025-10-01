# 🤖 Asistente de Agenda para Telegram

Este proyecto es un bot de Telegram diseñado para ayudar a grupos a organizar eventos y quedadas. Funciona como un asistente personal que permite a los usuarios ver, crear, unirse y abandonar eventos a través de una interfaz de menús interactivos.

Además, el bot integra un modelo de IA (Google Gemini) que permite procesar peticiones en lenguaje natural, como "crea un evento para cenar mañana a las 9 de la noche".

Una característica clave es el sistema de "vidas" por inactividad. El bot monitoriza la participación de los miembros del grupo y, tras un período de inactividad configurable, les resta "vidas". Si un usuario pierde todas sus vidas, es expulsado temporalmente del grupo, fomentando así una comunidad activa.

## ✨ Características Principales

- **Gestión de Eventos**: Crea, visualiza, inscríbete y date de baja de eventos.
- **Interfaz Intuitiva**: Menús con botones que guían al usuario en todo momento.
- **Inteligencia Artificial**: Procesamiento de lenguaje natural para crear y consultar eventos.
- **Sistema de Actividad**: Mecanismo de "vidas" para fomentar la participación y gestionar la inactividad.
- **Modular y Extensible**: Código organizado en `handlers` (lógica de Telegram) y `managers` (lógica de negocio) para facilitar su mantenimiento.
- **Persistencia de Datos**: Guarda la agenda y la base de datos de usuarios en archivos JSON.
- **Dockerizado**: Incluye un `Dockerfile` para un despliegue sencillo y consistente.

## 🚀 Puesta en Marcha

Sigue estos pasos para configurar y ejecutar el bot en tu propio entorno.

### 1. Prerrequisitos

- Python 3.10 o superior.
- Docker y Docker Compose (recomendado para un despliegue fácil).
- Una cuenta de Telegram y un token de Bot (consíguelo hablando con [@BotFather](https://t.me/BotFather)).
- Una API Key de Google Gemini para la funcionalidad de IA (opcional pero recomendado).

### 2. Configuración del Entorno

El bot se configura mediante variables de entorno. Crea un archivo llamado `.env` en la raíz del proyecto y añade las siguientes variables:

```bash
# El token que te dio @BotFather
TELEGRAM_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

# El ID del chat de grupo donde operará el bot.
# Puedes obtenerlo añadiendo temporalmente un bot como @userinfobot al grupo.
GROUP_CHAT_ID="-1001234567890"

# (Opcional) Tu API Key de Google Gemini.
# Si no la proporcionas, los comandos /ia no funcionarán.
GEMINI_API_KEY="AIzaSy..."

# (Opcional) Número de días de inactividad antes de perder una vida.
# Por defecto es 30.
INACTIVITY_DAYS=30
```

### 3. Instalación

Puedes instalar las dependencias directamente o usar Docker.

#### Opción A: Usando `pip` (Local)

1.  **Crea un entorno virtual (recomendado):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

#### Opción B: Usando Docker (Recomendado)

Con Docker, no necesitas instalar nada más en tu sistema.

1.  **Construye la imagen:**
    ```bash
    docker-compose build
    ```

### 4. Ejecución

#### Opción A: Ejecución Local

Asegúrate de tener el archivo `.env` configurado y el entorno virtual activado.

```bash
python3 main.py
```

#### Opción B: Ejecución con Docker

```bash
docker-compose up -d
```

Para ver los logs del contenedor:

```bash
docker-compose logs -f
```

Para detener el bot:
```bash
docker-compose down
```

## 📋 Uso del Bot

Una vez que el bot esté en funcionamiento y añadido a tu grupo, puedes interactuar con él usando los siguientes comandos:

-   `/start`: Muestra un mensaje de bienvenida.
-   `/agenda`: Despliega el menú principal para gestionar eventos. Desde aquí puedes:
    -   Ver la agenda de las próximas semanas.
    -   Crear un nuevo evento.
    -   Inscribirte a un evento existente.
    -   Darte de baja de un evento.
    -   Eliminar un evento que tú hayas creado.
-   `/ia <petición>`: Habla con la inteligencia artificial. Ejemplos:
    -   `/ia crea una quedada para jugar al pádel el sábado a las 11:00`
    -   `/ia ¿qué planes hay para este fin de semana?`

El bot también registrará automáticamente la actividad de cualquier miembro que envíe un mensaje, pulse un botón o se una a un evento.

## 📂 Estructura del Proyecto

El código está organizado de la siguiente manera para separar responsabilidades:

```
├── data/                  # Almacena los archivos JSON de la agenda y usuarios
├── src/
│   ├── config/            # Módulo de configuración (settings.py)
│   ├── handlers/          # Lógica de Telegram (comandos, callbacks, mensajes)
│   ├── managers/          # Lógica de negocio (gestión de agenda, usuarios, IA)
│   ├── __init__.py
│   └── ai_tools.py        # Definición de herramientas para la IA
├── .env.example           # Ejemplo de archivo de configuración
├── docker-compose.yml     # Orquestación de Docker
├── Dockerfile             # Definición del contenedor de Docker
├── main.py                # Punto de entrada de la aplicación
└── requirements.txt       # Dependencias de Python
```