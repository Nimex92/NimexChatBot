# NimexChatBot - Developer Guide

## 1. Project Overview
**NimexChatBot** is a modular Telegram bot designed for group management. It features an event agenda, AI-powered conversational capabilities (via Google Gemini), and automated user inactivity management. It acts as a helpful assistant with a specific regional personality (La Rioja, Spain).

## 2. Technical Architecture
The project follows a layered architecture to separate concerns:

-   **Handlers (`src/handlers/`)**: Interface layer. Receives Telegram updates (commands, messages, callbacks) and delegates logic.
    -   `general_handlers.py`: Core interactions (`/start`, mentions, AI chat).
    -   `agenda_handlers.py`: Agenda-specific interactions.
    -   `group_handlers.py`: Group administration tasks.
    -   `debate_handlers.py`: Functionality for managing debates.
    -   `level_handlers.py`: User leveling system interface.
-   **Managers (`src/managers/`)**: Business logic layer.
    -   `agenda_manager.py`: CRUD for events.
    -   `ai_manager.py`: Wraps Google Gemini API and handles tool/function calling.
    -   `user_manager.py`: Tracks user activity ("lives" system) and inactivity logic.
    -   `debate_manager.py`: Manages debate states and topics.
    -   `group_manager.py`: Handles group-specific logic.
-   **Data (`data/`)**: JSON-based persistence.
    -   `agenda.json`: Stores events.
    -   `users.json`: Stores user profiles and activity stats.
-   **Config (`src/config/`)**:
    -   `settings.py`: Loads environment variables and initializes constants.

## 3. Key Technologies
-   **Language**: Python 3.11+
-   **Telegram Framework**: `python-telegram-bot` (Async)
-   **AI**: `google-generativeai` (Gemini API)
-   **Scheduling**: `APScheduler` (for inactivity checks)
-   **Containerization**: Docker & Docker Compose
-   **Testing**: `pytest`

## 4. Setup & Configuration

### Environment Variables (`.env`)
Create a `.env` file based on `.env.example`:
-   `TELEGRAM_TOKEN`: Bot token from @BotFather.
-   `GEMINI_API_KEY`: API key from Google AI Studio.
-   `GROUP_CHAT_ID`: Target Telegram group ID.
-   `INACTIVITY_DAYS`: Days before a user loses a "life".

### Local Execution
```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python main.py
```

### Docker Execution
```bash
docker-compose up --build -d
```

## 5. Development & Testing
The project includes a test suite using `pytest`.
-   **Location**: `tests/`
-   **Fixtures**: `tests/conftest.py` handles setup/teardown of temporary JSON data files to avoid corrupting real data during tests.
-   **Running Tests**:
    ```bash
    pytest
    ```

## 6. AI Integration Details
The `ai_manager.py` is central to the bot's intelligence.
-   **Personality**: Defined via system instructions.
-   **Function Calling**: The AI can "call" Python functions (e.g., to create an agenda event) by outputting structured data which `ai_manager` intercepts and executes.

## 7. Current Status
-   **Stable**: Basic agenda, user tracking, and AI chat.
-   **In Progress/Experimental**: Debate system, leveling system (verify current status in code).
-   **Documentation**: Detailed technical docs available in `docs/documentacion_tecnica.md`.
