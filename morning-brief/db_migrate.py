#!/usr/bin/env python3
"""
Morning Brief — DB Migration (AI Curation & Impact Ranking)
Adds rank_section, rank_overall, ai_impact_reason, and curation_meta table.
"""
import sys
from db import get_conn, is_postgres

PG_MIGRATIONS = [
    """CREATE TABLE IF NOT EXISTS articles (
        id          SERIAL PRIMARY KEY,
        title       TEXT NOT NULL,
        link        TEXT UNIQUE NOT NULL,
        summary     TEXT,
        source      TEXT,
        fetched_at  TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS curation_meta (
        id               INT PRIMARY KEY DEFAULT 1,
        last_curated_at  TIMESTAMPTZ DEFAULT NOW(),
        is_curating      BOOLEAN DEFAULT FALSE
    )""",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS category VARCHAR(30) DEFAULT 'dev_hardware'",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS subcategory VARCHAR(30) DEFAULT 'dev_hardware'",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS importance_score INT DEFAULT 0",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS rank_section INT DEFAULT 99",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS rank_overall INT DEFAULT 99",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS hero_image TEXT",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS full_content TEXT",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS ai_summary TEXT",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS ai_impact_reason TEXT",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS read_time INT DEFAULT 3",
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS enriched BOOLEAN DEFAULT FALSE",
    "CREATE INDEX IF NOT EXISTS idx_category     ON articles(category)",
    "CREATE INDEX IF NOT EXISTS idx_rank_section ON articles(rank_section)",
    "CREATE INDEX IF NOT EXISTS idx_rank_overall ON articles(rank_overall)",
    "CREATE INDEX IF NOT EXISTS idx_enriched     ON articles(enriched)",
]

SQLITE_MIGRATIONS = [
    """CREATE TABLE IF NOT EXISTS articles (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        title            TEXT NOT NULL,
        link             TEXT UNIQUE NOT NULL,
        summary          TEXT,
        source           TEXT,
        category         VARCHAR(30) DEFAULT 'dev_hardware',
        subcategory      VARCHAR(30) DEFAULT 'dev_hardware',
        importance_score INT DEFAULT 0,
        rank_section     INT DEFAULT 99,
        rank_overall     INT DEFAULT 99,
        hero_image       TEXT,
        full_content     TEXT,
        ai_summary       TEXT,
        ai_impact_reason TEXT,
        read_time        INT DEFAULT 3,
        enriched         BOOLEAN DEFAULT FALSE,
        fetched_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS curation_meta (
        id               INTEGER PRIMARY KEY DEFAULT 1,
        last_curated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_curating      BOOLEAN DEFAULT FALSE
    )""",
    "ALTER TABLE articles ADD COLUMN category VARCHAR(30) DEFAULT 'dev_hardware'",
    "ALTER TABLE articles ADD COLUMN subcategory VARCHAR(30) DEFAULT 'dev_hardware'",
    "ALTER TABLE articles ADD COLUMN rank_section INT DEFAULT 99",
    "ALTER TABLE articles ADD COLUMN rank_overall INT DEFAULT 99",
    "ALTER TABLE articles ADD COLUMN ai_summary TEXT",
    "ALTER TABLE articles ADD COLUMN ai_impact_reason TEXT",
    "CREATE INDEX IF NOT EXISTS idx_category     ON articles(category)",
    "CREATE INDEX IF NOT EXISTS idx_rank_section ON articles(rank_section)",
    "CREATE INDEX IF NOT EXISTS idx_rank_overall ON articles(rank_overall)",
    "CREATE INDEX IF NOT EXISTS idx_enriched     ON articles(enriched)",
]


def run():
    conn = get_conn()
    cur = conn.cursor()
    migrations = PG_MIGRATIONS if is_postgres() else SQLITE_MIGRATIONS
    db_type = 'PostgreSQL' if is_postgres() else 'SQLite'
    print(f'Running migrations for {db_type}...')

    for sql in migrations:
        label = sql.strip()[:72].replace('\n', ' ')
        try:
            cur.execute(sql)
            conn.commit()
            print(f'  OK  {label}')
        except Exception as exc:
            if hasattr(conn, 'rollback'):
                conn.rollback()
            if 'duplicate column name' in str(exc).lower():
                print(f'  SKIP (exists) {label}')
            else:
                print(f'  ERR {label}\n      {exc}', file=sys.stderr)

    # Ensure single row in curation_meta
    try:
        cur.execute("INSERT INTO curation_meta (id, is_curating) VALUES (1, FALSE) ON CONFLICT (id) DO NOTHING")
        conn.commit()
    except Exception:
        pass

    conn.close()
    print('Migration complete.')


if __name__ == '__main__':
    run()
