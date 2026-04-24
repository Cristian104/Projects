import os
from flask import Flask

# Extensions & Models (import early for init)
from app.extensions import db, login_manager
from app.models import User, UserModuleAccess, AppEntry

# Blueprints (import after app creation to avoid circular issues)
from app.modules.auth.routes import auth_bp
from app.modules.dashboard.routes import dashboard_bp
from app.modules.gym.routes import gym_bp
from app.modules.tasks.routes import tasks_bp  # ← NEW: Tasks/Reminders module
from app.modules.nutrition.routes import nutrition_bp
from app.modules.nutrition import models as nutrition_models  # registers models with SQLAlchemy


def create_app():
    app = Flask(__name__)

    # --- SECURE CONFIG FROM .ENV ---
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    if not app.config['SECRET_KEY']:
        raise ValueError("❌ SECRET_KEY must be set in .env!")

    # Database Config — prefer DATABASE_URL (PostgreSQL on VPS), fallback to SQLite for local dev
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        db_path = os.path.join(app.instance_path, 'db.sqlite')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        os.makedirs(app.instance_path, exist_ok=True)

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # User Loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Module access context processor — injects uhm(module) into all templates
    @app.context_processor
    def inject_module_access():
        from flask_login import current_user
        from app.models import user_has_module
        if current_user.is_authenticated:
            return {'uhm': lambda m: user_has_module(current_user, m)}
        return {'uhm': lambda m: False}

    # --- REGISTER BLUEPRINTS ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(gym_bp)         # Your gym tracker module
    app.register_blueprint(tasks_bp)       # ← NEW: Separate reminders/to-do module
    app.register_blueprint(nutrition_bp)   # Nutrition tracking module

    # Start Bot Listener (only in prod or proper debug)
    if os.getenv('ENABLE_BOT') == 'true':
        if not app.debug or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
            from app.telegram_bot import start_bot_listener
            start_bot_listener(app)

    # Start Scheduler
    from app.scheduler import start_scheduler
    if not app.debug or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
        start_scheduler(app)

    return app