# AI Moderator

This project is a real-time AI moderator that uses Google Cloud STT for speech-to-text and Gemini 1.5 Flash for the AI brain.

## Project Overview

The project is built with Python 3.12 and FastAPI, and it's designed to be asynchronous to handle real-time communication efficiently. It uses native WebSockets for communication between the client and the server.

- **Backend:** Python 3.12, FastAPI
- **Real-time Communication:** Native WebSockets
- **Speech-to-Text (STT):** Google Cloud STT
- **AI Engine:** Gemini 1.5 Flash
- **Database:** SQLite (development), PostgreSQL (production)
- **Cache/Queue:** In-memory `asyncio.Queue`

The architecture is designed to minimize infrastructure management and enable fast development. The key goal is to achieve real-time responsiveness with a latency of less than 1 second. This is achieved through asynchronous streaming, optimistic UI updates, and streaming responses from the AI.

## Building and Running

There are no explicit build or run commands in the project yet. However, based on the project structure and dependencies, here's a likely scenario:

**TODO: Add specific commands for running the project.**

### Running the application (Likely):

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Set up the environment variables in a `.env` file (see `.env.example`). You'll need to provide your `GEMINI_API_KEY` and a `JWT_SECRET_KEY`.
3.  Run the application:
    ```bash
    uvicorn src.main:app --reload
    ```
    (Assuming the main FastAPI app instance is in `src/main.py`)

### Running tests:

```bash
pytest
```

## Development Conventions

- The project follows a 3-layered architecture: `api`, `core`, and `domain`.
- It uses `pydantic` for settings management, loading configuration from environment variables.
- Asynchronous programming with `async/await` is used throughout the project.
- Tests are written with `pytest`.
- The project uses an in-memory queue (`asyncio.Queue`) for caching and queuing, avoiding the need for external services like Redis in development.
- The project is configured to use SQLite in development and PostgreSQL in production. An ORM is likely used to abstract the database interactions, making the switch seamless.
