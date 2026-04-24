#!/usr/bin/env python3
"""
One-time migration: SQLite instance/db.sqlite → PostgreSQL (stacks-postgres)

Run this ONCE on the VPS before redeploying mybrain with DATABASE_URL set.

Usage (inside the mybrain container or with venv active):
    python3 migrate_to_postgres.py

Requires: POSTGRES_URL env var OR edit PG_URL below.
"""

import os
import sqlite3
import sys

import psycopg2
from psycopg2.extras import execute_values

SQLITE_PATH = os.path.join(os.path.dirname(__file__), "instance", "db.sqlite")
PG_URL = os.getenv("POSTGRES_URL", "postgresql://admin:stacks_secure_pass_2024@stacks-postgres:5432/mybrain")

# Migration order respects foreign keys
TABLES = [
    "user",
    "app_entry",
    "user_module_access",
    "task",
    "task_history",
    "gym_program",
    "gym_exercise_library",
    "gym_routine",
    "gym_exercise",
    "gym_log",
    "nutrition_plan",
    "nutrition_meal",
    "meal_ingredient",
    "water_log",
    "supplement_protocol",
    "supplement_log",
    "nutrition_log",
    "agent_message",
]


def get_pg_bool_columns(pg_cur, table):
    """Return set of column names that are boolean type in PostgreSQL."""
    pg_cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s AND data_type = 'boolean'
    """, (table,))
    return {row[0] for row in pg_cur.fetchall()}


def get_pg_varchar_lengths(pg_cur, table):
    """Return dict of column_name -> max_length for varchar columns."""
    pg_cur.execute("""
        SELECT column_name, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = %s AND data_type = 'character varying'
          AND character_maximum_length IS NOT NULL
    """, (table,))
    return {row[0]: row[1] for row in pg_cur.fetchall()}


def get_pg_int_columns(pg_cur, table):
    """Return set of column names that are integer type in PostgreSQL."""
    pg_cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s AND data_type IN ('integer', 'bigint', 'smallint')
    """, (table,))
    return {row[0] for row in pg_cur.fetchall()}


def get_sqlite_data(cur, table):
    cur.execute(f"SELECT * FROM \"{table}\"")
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return cols, rows


def coerce_row(row, cols, bool_cols, varchar_lengths, int_cols):
    """Convert SQLite values to PostgreSQL-compatible types."""
    result = []
    for val, col in zip(row, cols):
        if col in bool_cols and val is not None:
            val = bool(val)
        elif col in int_cols and val is not None and not isinstance(val, int):
            # SQLite dynamic typing may have stored a string in an integer column
            try:
                val = int(val)
            except (ValueError, TypeError):
                val = None
        elif col in varchar_lengths and isinstance(val, str):
            max_len = varchar_lengths[col]
            if len(val) > max_len:
                val = val[:max_len]
        result.append(val)
    return tuple(result)


def migrate():
    if not os.path.exists(SQLITE_PATH):
        print(f"SQLite not found at {SQLITE_PATH}")
        sys.exit(1)

    print(f"Connecting to SQLite: {SQLITE_PATH}")
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_cur = sqlite_conn.cursor()

    # Create schema via Flask app context first
    print("Creating PostgreSQL schema via SQLAlchemy...")
    sys.path.insert(0, os.path.dirname(__file__))
    os.environ["DATABASE_URL"] = PG_URL
    from app import create_app
    from app.extensions import db

    app = create_app()
    with app.app_context():
        db.create_all()
    print("Schema created.")

    # Open psycopg2 connection AFTER schema is committed
    print(f"Connecting to PostgreSQL: {PG_URL}")
    pg_conn = psycopg2.connect(PG_URL)
    pg_cur = pg_conn.cursor()

    for table in TABLES:
        try:
            cols, rows = get_sqlite_data(sqlite_cur, table)
        except sqlite3.OperationalError as e:
            print(f"  SKIP {table}: {e}")
            continue

        if not rows:
            print(f"  {table}: 0 rows — skipped")
            continue

        bool_cols = get_pg_bool_columns(pg_cur, table)
        varchar_lengths = get_pg_varchar_lengths(pg_cur, table)
        int_cols = get_pg_int_columns(pg_cur, table)

        coerced = [coerce_row(r, cols, bool_cols, varchar_lengths, int_cols) for r in rows]

        col_names = ",".join(f'"{c}"' for c in cols)
        sql = f'INSERT INTO "{table}" ({col_names}) VALUES %s ON CONFLICT DO NOTHING'

        try:
            execute_values(pg_cur, sql, coerced)
            pg_conn.commit()
            print(f"  {table}: {len(rows)} rows migrated")
        except Exception as e:
            pg_conn.rollback()
            print(f"  {table}: FAILED — {e}")

    # Reset sequences so auto-increment works correctly
    print("Resetting sequences...")
    for table in TABLES:
        try:
            pg_cur.execute(f"""
                SELECT setval(
                    pg_get_serial_sequence('"{table}"', 'id'),
                    COALESCE((SELECT MAX(id) FROM "{table}"), 1)
                )
            """)
        except Exception as e:
            print(f"  seq {table}: {e}")
            pg_conn.rollback()
    pg_conn.commit()

    sqlite_conn.close()
    pg_conn.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    migrate()
