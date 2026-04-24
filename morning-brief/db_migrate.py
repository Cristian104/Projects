#!/usr/bin/env python3
"""
Morning Brief — DB Migration
Adds new columns to the articles table for enrichment, categorisation, and scoring.
Run once: python db_migrate.py
"""
import os
import sys

import psycopg2

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://admin:stacks_secure_pass_2024@stacks-postgres:5432/news'
)

MIGRATIONS = [
    """CREATE TABLE IF NOT EXISTS articles (
        id          SERIAL PRIMARY KEY,
        title       TEXT NOT NULL,
        link        TEXT UNIQUE NOT NULL,
        summary     TEXT,
        source      TEXT,
        fetched_at  TIMESTAMPTZ DEFAULT NOW()
    )""",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS category VARCHAR(20) DEFAULT 'world'",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS importance_score INT DEFAULT 0",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS hero_image TEXT",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS full_content TEXT",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS read_time INT DEFAULT 3",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS enriched BOOLEAN DEFAULT FALSE",
    """UPDATE articles SET category='tech'
       WHERE source IN ('The Verge','Hacker News','TechCrunch','Wired','Ars Technica','The Register')
         AND category='world'""",
    "CREATE INDEX IF NOT EXISTS idx_category   ON articles(category)",
    "CREATE INDEX IF NOT EXISTS idx_importance ON articles(importance_score)",
    "CREATE INDEX IF NOT EXISTS idx_enriched   ON articles(enriched)",
    # Backfill: make existing world articles visible (importance=1).
    # Collector will re-score properly going forward.
    """UPDATE articles SET importance_score = 1
       WHERE category = 'world' AND importance_score = 0""",
]


def run():
    conn = psycopg2.connect(DATABASE_URL)
    cur  = conn.cursor()
    for sql in MIGRATIONS:
        label = sql.strip()[:72].replace('\n', ' ')
        try:
            cur.execute(sql)
            conn.commit()
            print(f'  OK  {label}')
        except Exception as exc:
            conn.rollback()
            print(f'  ERR {label}\n      {exc}', file=sys.stderr)
    conn.close()
    print('Migration complete.')


if __name__ == '__main__':
    run()
