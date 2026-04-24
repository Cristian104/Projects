## MyBrain Portal

MyBrain Portal is a personal dashboard application built with Flask and SQLAlchemy (for database interaction), designed to help manage various personal modules. It's typically deployed on a Virtual Private Server (VPS) and accessible via port `5000`.

!!! info Core Technologies
> -   **Backend**: Python 3.x, Flask, SQLAlchemy
> -   **Database**: Currently configured for `SQLite` for development, but designed for PostgreSQL in production setups.
> -   **Deployment**: Docker-compatible.

### Architectural Overview

The application's core is initialized via the `create_app()` factory function, which handles configuration, extension initialization, and blueprint registration.

#### Application Setup (`app/__init__.py`)

The Flask application is configured to load a `SECRET_KEY` from environment variables, which is crucial for session security.

```python
# --- SECURE CONFIG FROM .ENV ---
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("❌ SECRET_KEY must be set in .env!")

# Database Config
db_path = os.path.join(app.instance_path, 'db.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
```

!!! warning Production Database
> While the development setup uses `sqlite:///{instance_path}/db.sqlite`, production environments should utilize a robust database like PostgreSQL for data integrity and scalability. Ensure your `.env` config reflects this.

Extensions like `SQLAlchemy`'s `db` and `Flask-Login`'s `login_manager` are initialized early.

#### Registered Blueprints

The portal modularizes its features using Flask Blueprints:

-   `auth_bp`: User authentication and session management.
-   `dashboard_bp`: The main dashboard view.
-   `gym_bp`: Gym tracking module. (obsidian/mybrain/gym-module)
-   `tasks_bp`: Personal tasks and reminders.
-   `nutrition_bp`: Nutrition tracking. (obsidian/mybrain/nutrition-module)

```python
# --- REGISTER BLUEPRINTS ---
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(gym_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(nutrition_bp)
```

#### Special Features

-   **Module Access Control**: A context processor `inject_module_access` is used to expose `uhm(module)` to templates, allowing dynamic control over module visibility based on user permissions.
-   **Bot Listener**: The application can integrate with a Telegram bot or similar, activated conditionally via `ENABLE_BOT='true'` in the environment.
-   **Scheduler**: An internal scheduler (`start_scheduler`) manages background tasks.

```python
# Start Bot Listener (only in prod or proper debug)
if os.getenv('ENABLE_BOT') == 'true':
    # ...
    from app.telegram_bot import start_bot_listener
    start_bot_listener(app)

# Start Scheduler
from app.scheduler import start_scheduler
if not app.debug or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
    start_scheduler(app)
```

### Data Models (`app/models.py`)

The application's data structure is defined using SQLAlchemy models.

-   `User`: Represents portal users, linked to tasks and module access.
    ```python
    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(150), unique=True, nullable=False)
        email = db.Column(db.String(150), unique=True, nullable=True) # Critical field
        password = db.Column(db.String(150), nullable=False)
        # ...
    ```
    !!! note User Email Field
    > The `email` field is crucial for user identification and was previously missing, leading to login issues. Ensure it's present and correctly configured.

-   `Task`: Stores individual tasks, with attributes for content, priority, category, completion status, due dates, and recurrence. Supports habit tracking (`is_habit`).
-   `TaskHistory`: Records completion history for tasks, particularly useful for habit tracking.
-   `UserModuleAccess`: Controls which modules (`gym`, `nutrition`, `tasks`, `applications`) a specific user has enabled. The `user_has_module` function checks this access.
-   `AgentMessage`: Logs messages from various integrated agents (e.g., `peccata`) for audit and interaction history.
-   `AppEntry`: Defines entries for the "Applications Launcher" module, including `name`, `url`, and `icon`.

### Deployment

The MyBrain Portal is designed to be accessible on `VPS_IP_ADDRESS:5000`. Ensure your firewall rules permit traffic on this port and that a reverse proxy (e.g., obsidian/infrastructure/nginx) is configured for production use.

## Related

-   obsidian/mybrain/overview
-   obsidian/mybrain/development
-   obsidian/mybrain/gym-module
-   obsidian/mybrain/nutrition-module
-   obsidian/infrastructure/nginx
-   PostgreSQL
-   Flask
-   Peccata