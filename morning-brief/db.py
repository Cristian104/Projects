"""
Morning Brief — Unified Database Interface
Supports both PostgreSQL (production/docker) and SQLite (local dev fallback).
"""
import os
import re
import sqlite3
from pathlib import Path

import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
DEFAULT_SQLITE_PATH = Path(__file__).parent / 'news.db'


def is_postgres() -> bool:
    return DATABASE_URL.startswith('postgres')


def get_conn():
    if is_postgres():
        return psycopg2.connect(DATABASE_URL)
    else:
        conn = sqlite3.connect(str(DEFAULT_SQLITE_PATH))
        conn.row_factory = sqlite3.Row
        return conn


def get_cursor(conn):
    if is_postgres():
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        return conn.cursor()


def query(conn, sql: str, params=()):
    """
    Executes a query converting parameter markers and syntax as needed:
      - %s -> ? for SQLite
      - NOW() - %s::interval -> datetime('now', '-' || ? || ' hours') for SQLite
      - ON CONFLICT (link) DO NOTHING -> INSERT OR IGNORE for SQLite
    """
    cur = get_cursor(conn)
    if not is_postgres():
        # Convert syntax for SQLite
        sql_sqlite = sql
        if 'ON CONFLICT' in sql_sqlite and 'INSERT INTO' in sql_sqlite:
            sql_sqlite = sql_sqlite.replace('INSERT INTO', 'INSERT OR IGNORE INTO').replace('ON CONFLICT (link) DO NOTHING', '')
        
        # Replace NOW() - %s::interval or NOW() - INTERVAL '24 hours'
        sql_sqlite = re.sub(r"NOW\(\)\s*-\s*%s::interval", "datetime('now', '-' || ? || ' hours')", sql_sqlite, flags=re.IGNORECASE)
        sql_sqlite = re.sub(r"NOW\(\)\s*-\s*INTERVAL\s*'(\d+)\s*hours'", r"datetime('now', '-\1 hours')", sql_sqlite, flags=re.IGNORECASE)
        sql_sqlite = re.sub(r"NOW\(\)\s*-\s*INTERVAL\s*'(\d+)\s*days'", r"datetime('now', '-\1 days')", sql_sqlite, flags=re.IGNORECASE)
        
        # Convert remaining %s to ?
        sql_sqlite = sql_sqlite.replace('%s', '?')
        cur.execute(sql_sqlite, params)
    else:
        cur.execute(sql, params)
    return cur
