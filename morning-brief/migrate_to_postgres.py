#!/usr/bin/env python3
"""
One-time migration: morning-brief SQLite news.db → PostgreSQL stacks-postgres/news

Run on VPS:
    ~/stacks/morning-brief/.venv/bin/python3 ~/stacks/morning-brief/migrate_to_postgres.py
"""
import os
import sqlite3
import psycopg2

SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'news.db')
PG_URL = os.getenv('DATABASE_URL', 'postgresql://admin:stacks_secure_pass_2024@localhost:5434/news')


def migrate():
    print(f'Reading SQLite: {SQLITE_PATH}')
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    rows = sqlite_conn.execute('SELECT title, link, summary, source, fetched_at FROM articles').fetchall()
    print(f'Found {len(rows)} articles')
    sqlite_conn.close()

    print(f'Connecting to PostgreSQL: {PG_URL}')
    pg_conn = psycopg2.connect(PG_URL)
    pg_cur = pg_conn.cursor()

    # Create table if not exists
    pg_cur.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id         SERIAL PRIMARY KEY,
            title      TEXT    NOT NULL,
            link       TEXT    NOT NULL UNIQUE,
            summary    TEXT,
            source     TEXT    NOT NULL,
            fetched_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''')
    pg_cur.execute('CREATE INDEX IF NOT EXISTS idx_source ON articles(source)')
    pg_cur.execute('CREATE INDEX IF NOT EXISTS idx_fetched ON articles(fetched_at)')
    pg_conn.commit()

    inserted = 0
    skipped = 0
    for r in rows:
        pg_cur.execute(
            'INSERT INTO articles (title, link, summary, source, fetched_at) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (link) DO NOTHING',
            (r['title'], r['link'], r['summary'], r['source'], r['fetched_at'])
        )
        if pg_cur.rowcount:
            inserted += 1
        else:
            skipped += 1

    pg_conn.commit()
    pg_conn.close()
    print(f'Done — {inserted} inserted, {skipped} skipped (duplicates).')


if __name__ == '__main__':
    migrate()
