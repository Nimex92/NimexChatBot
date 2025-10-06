# Documentación Técnica: NimexChatBot

## 1. Introducción

**NimexChatBot** es un asistente de Telegram versátil y modular, diseñado para la gestión de grupos. Su propósito principal es fomentar la interacción y facilitar la organización de eventos. El bot, con una personalidad amigable y regional (de La Rioja, España), integra un sistema de agenda, capacidades de inteligencia artificial conversacional y un mecanismo de gestión de actividad de usuarios.

El proyecto está construido en Python y diseñado para ser desplegado fácilmente como un contenedor Docker, garantizando la portabilidad y la persistencia de los datos.

### 1.1. Requerimientos Principales

*   **Plataforma:** Python 3.11
*   **Framework del Bot:** `python-telegram-bot`
*   **Inteligencia Artificial:** `google-generativeai` (Gemini)
*   **Programación de Tareas:** `APScheduler`
*   **Entorno de Ejecución:** Docker
*   **Dependencias clave:** Ver `requirements.txt` para la lista completa.

## 2. Arquitectura y Diseño

El bot sigue una arquitectura modular y de varias capas que separa las responsabilidades, facilitando su mantenimiento y escalabilidad.

### 2.1. Estructura de Directorios

La estructura del proyecto está organizada de la siguiente manera:

```
NimexChatBot/
├── data/                  # Datos persistentes (JSON)
│   ├── agenda.json
│   └── users.json
├── src/                   # Código fuente principal
│   ├── config/            # Módulo de configuración
│   │   └── settings.py
│   ├── handlers/          # Manejadores de eventos de Telegram
│   │   ├── agenda_handlers.py
│   │   └── general_handlers.py
│   └── managers/          # Lógica de negocio y acceso a datos
│       ├── agenda_manager.py
│       ├── ai_manager.py
│       └── user_manager.py
├── .env.example           # Plantilla de variables de entorno
├── docker-compose.yml     # Orquestación del contenedor
├── Dockerfile             # Definición de la imagen Docker
├── main.py                # Punto de entrada de la aplicación
└── requirements.txt       # Dependencias de Python
```

### 2.2. Diseño de Capas

1.  **Capa de Presentación (Handlers):** Los módulos en `src/handlers/` son responsables de recibir y procesar las actualizaciones de la API de Telegram (comandos, mensajes, callbacks de botones). Su función es interpretar la entrada del usuario y llamar a la capa de lógica de negocio. No contienen lógica de negocio compleja.

2.  **Capa de Lógica de Negocio (Managers):** Los módulos en `src/managers/` encapsulan la lógica principal de la aplicación.
    *   `agenda_manager.py`: Gestiona todas las operaciones CRUD (Crear, Leer, Actualizar, Borrar) para los eventos. Es el único módulo que interactúa directamente con `agenda.json`.
    *   `user_manager.py`: Gestiona la actividad de los usuarios, incluyendo el sistema de "vidas" por inactividad. Es el único que interactúa con `users.json`.
    *   `ai_manager.py`: Orquesta la interacción con la IA de Gemini, incluyendo la gestión de la personalidad del bot y el uso de herramientas (function calling).

3.  **Capa de Datos (Data):** La persistencia de los datos se logra mediante archivos JSON en el directorio `data/`. Este directorio se monta como un volumen en Docker para que los datos sobrevivan a los reinicios del contenedor.
    *   `agenda.json`: Almacena los eventos.
    *   `users.json`: Almacena la información y el estado de actividad de los usuarios.

4.  **Punto de Entrada (`main.py`):** Orquesta el arranque del bot. Inicializa los managers, configura los manejadores de eventos (handlers) y pone en marcha el bot y las tareas programadas (jobs).

## 3. Componentes Principales

### `main.py`
*   **Responsabilidad:** Punto de entrada de la aplicación.
*   **Funciones Clave:**
    *   Carga la configuración y los datos iniciales (`agenda.json`, `users.json`).
    *   Crea la instancia de la aplicación del bot de Telegram.
    *   Registra todos los manejadores de comandos y mensajes.
    *   Configura y lanza la tarea diaria (`job_queue`) para la comprobación de inactividad de usuarios.
    *   Inicia el polling del bot para recibir actualizaciones de Telegram.

### `src/config/settings.py`
*   **Responsabilidad:** Centralizar todas las variables de configuración.
*   **Funciones Clave:**
    *   Carga las variables de entorno desde el archivo `.env` (tokens, IDs de chat, etc.).
    *   Configura el cliente de la API de Google Gemini.
    *   Define constantes utilizadas en todo el proyecto, como las rutas a los archivos de datos.

### `src/managers/agenda_manager.py`
*   **Responsabilidad:** Gestionar la lógica de la agenda de eventos.
*   **Funciones Clave:**
    *   `cargar_agenda()` / `guardar_agenda()`: Serializa y deserializa el estado de la agenda desde/hacia `agenda.json`.
    *   `crear_evento()`, `desactivar_evento()`: Lógica para añadir y eliminar (lógicamente) eventos.
    *   `inscribir_usuario()`, `desinscribir_usuario()`: Gestiona la lista de asistentes a un evento.
    *   `obtener_eventos_activos()`: Devuelve los eventos filtrados por rango de fechas.

### `src/managers/user_manager.py`
*   **Responsabilidad:** Gestionar la base de datos de usuarios y su actividad.
*   **Funciones Clave:**
    *   `load_users()` / `save_users()`: Carga y guarda la base de datos de usuarios.
    *   `update_user_activity()`: Actualiza la marca de tiempo de "última actividad" de un usuario.
    *   `check_inactivity_job()`: Tarea programada que reduce "vidas" a los usuarios inactivos y los expulsa si llegan a cero.

### `src/managers/ai_manager.py`
*   **Responsabilidad:** Interfaz con el modelo de IA generativa (Gemini).
*   **Funciones Clave:**
    *   Define la `system_instruction` que dota al bot de su personalidad y reglas de comportamiento.
    *   Gestiona el "function calling", permitiendo a la IA invocar funciones de Python (ej. `crear_evento`) para realizar acciones.
    *   `process_user_prompt()`: Procesa la entrada del usuario, la envía a la IA y maneja la respuesta, ya sea texto o una llamada a una función.

### `src/handlers/`
*   **Responsabilidad:** Conectar las interacciones del usuario en Telegram con la lógica de negocio.
*   `general_handlers.py`: Contiene manejadores para eventos generales como `/start`, bienvenida a nuevos miembros y, crucialmente, `handle_mention` para las interacciones con la IA.
*   `agenda_handlers.py`: Contiene todos los manejadores para el comando `/agenda`, incluyendo el menú principal y el flujo de callbacks para crear, ver o inscribirse en eventos.

## 4. Flujos de Interacción

### 4.1. Flujo: Creación de un Evento (vía IA)

1.  **Usuario:** Menciona al bot en un grupo: `@NimexChatBot crea una cena para el viernes a las 21:00`.
2.  **Telegram:** Envía una actualización de mensaje al bot.
3.  **`main.py`:** El `MessageHandler` para menciones en grupo se activa.
4.  **`general_handlers.handle_mention()`:** Extrae el texto del mensaje y el ID del usuario.
5.  **`ai_manager.process_user_prompt()`:** Envía el texto a la API de Gemini.
6.  **Gemini:** Analiza el texto y determina que debe usar la herramienta `crear_evento`. Devuelve una llamada a función con los parámetros extraídos: `crear_evento(fecha='YYYY-MM-DD', hora='21:00', titulo='Cena', creador_id=12345)`.
7.  **`ai_manager`:** Recibe la llamada, busca la función `crear_evento` en `AVAILABLE_TOOLS` y la ejecuta.
8.  **`agenda_manager.crear_evento()`:** Añade el evento al diccionario de la agenda y llama a `guardar_agenda()`.
9.  **`ai_manager`:** Envía el resultado de la ejecución de la función de vuelta a Gemini.
10. **Gemini:** Genera una respuesta de texto confirmando la creación del evento (ej. "¡Listo, majo! He apuntado la cena para el viernes.").
11. **`ai_manager`:** Devuelve este texto al `general_handlers`.
12. **`general_handlers`:** Envía la respuesta final al chat de Telegram.

### 4.2. Flujo: Comprobación de Inactividad

1.  **`main.py`:** La `job_queue` (planificador de tareas) ejecuta la función `user_manager.check_inactivity_job()` a la hora programada (diariamente a las 04:00).
2.  **`user_manager.check_inactivity_job()`:** Itera sobre todos los usuarios en `users_db`.
3.  Para cada usuario, compara la fecha de `last_seen` con la fecha actual.
4.  Si la diferencia supera `INACTIVITY_DAYS`, reduce en 1 el contador de `lives` del usuario y actualiza su `last_seen` a la fecha actual.
5.  Intenta notificar al usuario por mensaje privado sobre la vida perdida.
6.  Si el contador de `lives` llega a 0, el ID del usuario se añade a una lista `users_to_kick`.
7.  Al final del bucle, itera sobre `users_to_kick`, expulsa a cada usuario del grupo y lo "des-banea" para permitirle volver a unirse.
8.  Llama a `save_users()` para persistir todos los cambios.

## 5. Configuración y Despliegue

El proyecto está diseñado para ser desplegado con Docker y Docker Compose.

### Pasos para el Despliegue:

1.  **Clonar el Repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd NimexChatBot
    ```

2.  **Crear el Archivo de Entorno:**
    Copia el archivo de ejemplo `.env.example` a `.env`.
    ```bash
    cp .env.example .env
    ```
    Edita el archivo `.env` y rellena las siguientes variables:
    *   `TELEGRAM_TOKEN`: El token de tu bot de Telegram.
    *   `GEMINI_API_KEY`: Tu clave de API de Google AI Studio.
    *   `GROUP_CHAT_ID`: El ID del chat de grupo donde operará el bot.
    *   `INACTIVITY_DAYS`: (Opcional) Número de días de inactividad para perder una vida.

3.  **Construir y Ejecutar el Contenedor:**
    Utiliza Docker Compose para construir la imagen y lanzar el servicio en segundo plano.
    ```bash
    docker-compose up --build -d
    ```
    *   `--build`: Fuerza la reconstrucción de la imagen si el `Dockerfile` o el código han cambiado.
    *   `-d`: Ejecuta el contenedor en modo "detached" (en segundo plano).

4.  **Verificar el Funcionamiento:**
    Puedes ver los logs del contenedor para asegurarte de que ha arrancado correctamente.
    ```bash
    docker-compose logs -f
    ```
    Deberías ver el mensaje: `🤖 Bot modular arrancado. Escuchando menciones...`

## 6. Manual de Usuario

### Comandos Principales
*   `/start`: Muestra un mensaje de bienvenida y una breve explicación de las funciones del bot.
*   `/agenda`: Despliega un menú interactivo con las siguientes opciones:
    *   **Ver agenda:** Muestra los eventos programados.
    *   **Crear un evento:** Inicia un asistente paso a paso para crear un nuevo evento.
    *   **Inscribirme a un evento:** Muestra una lista de eventos a los que te puedes apuntar.
    *   **Darme de baja:** Muestra los eventos en los que estás inscrito para que puedas borrarte.
    *   **Eliminar evento creado:** Permite al creador de un evento eliminarlo.

### Interacción con IA
*   **Menciones:** En un grupo, puedes hablar directamente con el bot mencionándolo (`@nombre_del_bot`) seguido de tu petición en lenguaje natural.
    *   **Ejemplos:**
        *   `@NimexChatBot ¿qué planes hay para el fin de semana?`
        *   `@NimexChatBot apunta una comida para el domingo a las 14:00.`
        *   `@NimexChatBot ¿cómo funciona el sistema de vidas?`

## 7. Pruebas

Actualmente, el proyecto **no cuenta con un framework de pruebas automatizadas**. La verificación se ha realizado de forma manual.

**Recomendación:** Sería altamente beneficioso implementar:
*   **Pruebas Unitarias (Unit Tests):** Para los módulos `managers`. Se podría usar `pytest` para probar funciones individuales en aislamiento (ej. `test_crear_evento`, `test_inscribir_usuario`), utilizando datos de prueba (fixtures) en lugar de los archivos JSON reales.
*   **Pruebas de Integración (Integration Tests):** Para los `handlers`, para asegurar que la interacción entre los manejadores y los gestores funciona como se espera.

## 8. Futuras Mejoras

*   **Base de Datos Robusta:** Migrar la persistencia de datos de archivos JSON a una base de datos más sólida como **SQLite** (para simplicidad) o **PostgreSQL** (para escalabilidad). Esto mejoraría el rendimiento y la concurrencia.
*   **Gestión de Errores Avanzada:** Implementar un sistema más detallado de logging y notificación de errores para el administrador del bot.
*   **Más Herramientas para la IA:** Ampliar las capacidades de "function calling" de la IA para interactuar con otras APIs (ej. previsión del tiempo, buscar noticias) o para realizar acciones más complejas dentro del bot.
*   **Panel de Administración Web:** Crear una interfaz web simple para que el administrador pueda ver estadísticas de uso, gestionar usuarios o configurar el bot sin necesidad de editar archivos o variables de entorno.
*   **Localización (i18n):** Aunque el bot tiene un "sabor" español, el texto está codificado directamente. Se podría implementar un sistema de internacionalización para soportar múltiples idiomas.
