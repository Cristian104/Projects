"""Runs db.create_all() to create any new tables before gunicorn starts.
Also runs ALTER TABLE for new columns on existing tables (SQLite-safe)."""
import os
import sqlite3

# Load .env if python-dotenv is available (dev mode); in Docker env vars come from env_file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app, db
# Import all models so SQLAlchemy registers them
from app.models import User, Task, UserModuleAccess, AppEntry, AgentMessage
from app.modules.gym.models import GymProgram, GymRoutine, GymExercise, GymLog, GymExerciseLibrary
from app.modules.nutrition.models import (NutritionPlan, NutritionMeal, MealIngredient,
                                           NutritionLog, WaterLog, SupplementProtocol, SupplementLog)

app = create_app()

with app.app_context():
    db.create_all()
    print("✅ New tables created.")

    # SQLite ALTER TABLE for new columns on existing tables
    db_path = os.path.join(app.instance_path, 'db.sqlite')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    def column_exists(table, column):
        cursor.execute(f"PRAGMA table_info({table})")
        return any(row[1] == column for row in cursor.fetchall())

    # GymExercise new columns
    gym_exercise_cols = [
        ("notes", "VARCHAR(300)"),
        ("is_per_side", "BOOLEAN DEFAULT 0"),
        ("rir_target", "INTEGER"),
        ("has_drop_set", "BOOLEAN DEFAULT 0"),
        ("order_index", "INTEGER DEFAULT 0"),
    ]
    for col, typedef in gym_exercise_cols:
        if not column_exists("gym_exercise", col):
            cursor.execute(f"ALTER TABLE gym_exercise ADD COLUMN {col} {typedef}")
            print(f"  + gym_exercise.{col}")

    # GymLog new columns
    gym_log_cols = [
        ("set_number", "INTEGER DEFAULT 1"),
        ("session_id", "VARCHAR(36)"),
    ]
    for col, typedef in gym_log_cols:
        if not column_exists("gym_log", col):
            cursor.execute(f"ALTER TABLE gym_log ADD COLUMN {col} {typedef}")
            print(f"  + gym_log.{col}")

    conn.commit()
    conn.close()
    print("✅ Database schema up to date.")

    # Fix app icons: Docker brand icons need 'fab fa-docker' not 'fas fa-docker'
    brand_icon_map = {
        'fa-docker':  'fab fa-docker',
        'fa-github':  'fab fa-github',
        'fa-gitlab':  'fab fa-gitlab',
        'fa-slack':   'fab fa-slack',
        'fa-discord': 'fab fa-discord',
        'fa-telegram': 'fab fa-telegram',
        'fa-linux':   'fab fa-linux',
        'fa-windows': 'fab fa-windows',
        'fa-apple':   'fab fa-apple',
        'fa-node':    'fab fa-node',
        'fa-python':  'fab fa-python',
    }
    apps = AppEntry.query.all()
    fixed = 0
    for app_entry in apps:
        if app_entry.icon and app_entry.icon in brand_icon_map:
            app_entry.icon = brand_icon_map[app_entry.icon]
            fixed += 1
    if fixed:
        db.session.commit()
        print(f"  + Fixed {fixed} app brand icon(s)")
