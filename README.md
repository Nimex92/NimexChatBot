# NimexChatBot

NimexChatBot es un bot de Telegram multifuncional diseñado para la gestión de grupos, organización de agenda y con capacidades de inteligencia artificial.

## Características

- **Gestión de Agenda**: Permite a los usuarios gestionar su propia agenda, añadiendo, eliminando y consultando eventos.
- **Inteligencia Artificial**: Integrado con Gemini, el bot puede responder a menciones en el grupo con respuestas generadas por IA.
- **Gestión de Inactividad**: Expulsa automáticamente a los miembros inactivos del grupo después de un período de tiempo configurable.
- **Mensajes de Bienvenida**: Da la bienvenida a los nuevos miembros que se unen al grupo.

## Instalación

1.  Clona este repositorio:
    ```bash
    git clone https://github.com/tu_usuario/NimexChatBot.git
    ```
2.  Navega al directorio del proyecto:
    ```bash
    cd NimexChatBot
    ```
3.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```

## Uso

1.  Crea un archivo `.env` a partir de `.env.example` y completa las variables de entorno.
2.  Ejecuta el bot:
    ```bash
    python main.py
    ```

## Configuración

El bot se configura a través de variables de entorno. Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

- `TELEGRAM_TOKEN`: El token de tu bot de Telegram.
- `GEMINI_API_KEY`: Tu clave de API de Gemini.
- `GROUP_CHAT_ID`: El ID del grupo de Telegram donde operará el bot.
- `INACTIVITY_DAYS`: El número de días de inactividad antes de que un usuario sea expulsado.
