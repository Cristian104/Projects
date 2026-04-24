# MyBrain Portal: Development Guide

The MyBrain Portal (`services/mybrain-portal/`) is a personal web dashboard built with Flask, designed to track gym progress, nutrition, and general tasks. This document outlines local setup, environment variable management, application structure, and deployment considerations.

## Local Development Setup

!!! tip
> For rapid local development, the MyBrain Portal is designed to run directly on your host system, enabling hot-reloading and simpler debugging without Docker overhead.

To launch the MyBrain Portal locally, use the provided `make` command:

```bash
make mybrain
```

This command will typically activate a virtual environment and execute the `run.py` script. The application will be accessible at `http://localhost:5000`.

Alternatively, you can run it manually:

```bash
cd services/mybrain-portal
source venv/bin/activate # Or your preferred virtual environment activation
python run.py
```

### `run.py` Execution Details

The `run.py` script serves as the development entry point and handles critical setup steps:

1.  **Environment Variable Loading**:
    ```python
    from dotenv import load_dotenv
    load_dotenv(override=True)
    ```
    This ensures that `.env` variables (see #Environment Variables) are loaded *before* the Flask application starts, which is crucial for configurations like `TELEGRAM_BOT_TOKEN`. The `override=True` flag ensures system-level environment variables don't prevent `.env` file variables from being set.

2.  **Application Initialization**:
    ```python
    from app import create_app, db
    from app.scheduler import start_scheduler

    app = create_app()
    ```
    The application uses the Flask application factory pattern (`create_app`) and initializes the database (`db`). It also integrates with a scheduler (`app.scheduler.start_scheduler`) for background tasks.

3.  **Database & Scheduler**:
    ```python
    with app.app_context():
        db.create_all()  # Create tables if needed
        start_scheduler(app) # Start scheduler + bot listener
    ```
    Upon startup, `db.create_all()` will create any missing database tables defined in the SQLAlchemy models. The `start_scheduler` function initializes background jobs or listeners (e.g., for Telegram bots) using `Flask-APScheduler`.

4.  **Debug Mode**:
    ```python
    app.run(
        debug=True,
        use_reloader=False,  # Prevents double-starting bot/scheduler threads
        host='0.0.0.0',       # Accessible from your network
        port=5000
    )
    ```
    `debug=True` enables Flask's debugging features. `use_reloader=False` is critical to prevent the `Flask-APScheduler` and any Telegram bot listeners from being initialized twice, which can lead to unexpected behavior or errors. The app listens on `0.0.0.0:5000`.

### Key Dependencies

The `services/mybrain-portal/requirements.txt` specifies core libraries:

-   `Flask`: Web framework.
-   `SQLAlchemy`, `Flask-SQLAlchemy`, `psycopg2-binary`: Database ORM for PostgreSQL.
-   `APScheduler`, `Flask-APScheduler`: For background tasks and scheduled jobs.
-   `pyTelegramBotAPI`: Integration with Telegram (e.g., for notifications or bot control).
-   `google-genai`: For integrating with Google's generative AI models.
-   `PyPDF2`: For PDF processing (e.g., parsing documents for information).
-   `docker`: For interacting with Docker (e.g., managing containers).

## Environment Variables

!!! warning
> Never commit `.env` files to version control. Use `.env.example` as a template for required variables.

Environment variables are loaded from multiple `.env` files in a hierarchical manner:

-   `~/stacks/.env`: Shared variables (e.g., global `GEMINI_API_KEY`, common Telegram tokens).
-   `~/stacks/services/mybrain-portal/.env`: MyBrain-specific variables (e.g., `SECRET_KEY`, specific Telegram bot tokens or chat IDs).

Ensure your `services/mybrain-portal/.env` contains, at minimum:
```
SECRET_KEY=YOUR_SUPER_SECRET_KEY_HERE
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID
DATABASE_URL=postgresql://admin:devpassword@localhost:5433/remastered_core
```

!!! info
> The local development database URL typically points to `localhost:5433`, as set up by `make up`. For production, it defaults to `localhost:5432`.

## Flask Application Structure

The MyBrain Portal follows a standard Flask application package structure:

-   `app/`: The main Python package for the Flask application.
    -   `__init__.py`: Contains the `create_app()` factory function, which initializes the Flask app, configures extensions, and registers blueprints.
    -   `scheduler.py`: Houses the `start_scheduler()` function and defines scheduled tasks or bot listeners.
    -   `models.py`: Defines SQLAlchemy database models.
    -   `routes/`: Directory for blueprints defining different sections of the application (e.g., `gym_routes.py`, `nutrition_routes.py`).
    -   `templates/`: HTML Jinja2 templates.
    -   `static/`: CSS, JavaScript, and other static assets.

## VPS Deployment via GitHub Actions

The entire monorepo, including the MyBrain Portal, is deployed to the VPS via a GitHub Actions workflow whenever changes are pushed to the `main` branch.

```
git push → GitHub (Cristian104/stacks) → GitHub Actions → VPS (76.13.251.113)
```

> [!CAUTION]
> **Do NOT** SSH into the VPS to edit code directly. All code changes must follow the `git push` workflow to ensure consistency and maintainability.

The MyBrain Portal runs on port `5000` in the production environment on the VPS.

## Related

-   CLAUDE
-   Nginx Configuration
-   Monitoring Services
-   MyBrain Portal Overview
---