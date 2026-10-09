"""Intelligence Feed — Flask web app v2. Port 8009."""
import html
import os
import re

import psycopg2
import psycopg2.extras
from flask import Flask, abort, jsonify, render_template, request

app = Flask(__name__)
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://admin:stacks_secure_pass_2024@stacks-postgres:5432/news'
)

TECH_SOURCES = {'The Verge', 'Hacker News', 'TechCrunch', 'Wired', 'Ars Technica', 'The Register'}


# ── Helpers ────────────────────────────────────────────────────────────────────
def _db():
    return psycopg2.connect(DATABASE_URL)


def _clean_html(text: str, maxlen: int = 280) -> str:
    text = re.sub(r'<[^>]+>', '', text or '')
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return (text[:maxlen] + '…') if len(text) > maxlen else text


def _source_slug(name: str) -> str:
    return re.sub(r'[^a-z0-9]', '-', name.lower())


def _fmt_article(r) -> dict:
    fa = r['fetched_at']
    return {
        'id':          r['id'],
        'title':       r['title'],
        'link':        r['link'],
        'summary':     _clean_html(r['summary'], 280),
        'source':      r['source'],
        'source_slug': _source_slug(r['source']),
        'category':    r.get('category') or 'world',
        'importance':  r.get('importance_score') or 0,
        'hero_image':  r.get('hero_image'),
        'read_time':   r.get('read_time') or 3,
        'fetched_at':  str(fa or '')[:16].replace('T', ' '),
    }


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    tab   = request.args.get('tab', 'all')
    if tab not in ('all', 'tech', 'world', 'entertainment'):
        tab = 'all'
    hours = max(1, min(168, int(request.args.get('hours', 24))))
    interval = f'{hours} hours'

    conn = _db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if tab == 'all':
        where = "(category='tech' OR category='entertainment' OR importance_score >= 1)"
    elif tab == 'tech':
        where = "category='tech'"
    elif tab == 'entertainment':
        where = "category='entertainment'"
    else:  # world
        where = "category='world' AND importance_score >= 1"

    cur.execute(f"""
        SELECT id, title, link, summary, source, category,
               importance_score, hero_image, read_time, fetched_at
        FROM articles
        WHERE {where}
          AND fetched_at >= NOW() - %s::interval
        ORDER BY
          CASE WHEN category='world' AND importance_score >= 2 THEN 0 ELSE 1 END,
          fetched_at DESC
        LIMIT 120
    """, (interval,))
    rows = cur.fetchall()

    # Stats
    cur.execute("""
        SELECT
          (SELECT COUNT(*) FROM articles
           WHERE fetched_at >= NOW() - INTERVAL '24 hours') AS today,
          (SELECT COUNT(*) FROM articles
           WHERE category='tech' AND fetched_at >= NOW() - INTERVAL '24 hours') AS tech_today,
          (SELECT COUNT(*) FROM articles) AS total,
          (SELECT MAX(fetched_at) FROM articles) AS last_fetch
    """)
    _sr    = cur.fetchone()
    stats  = dict(_sr) if _sr else {}
    if stats.get('last_fetch'):
        stats['last_fetch'] = str(stats['last_fetch'])[:16].replace('T', ' ')

    # Sources
    cur.execute('SELECT DISTINCT source FROM articles ORDER BY source')
    sources = [r['source'] for r in cur.fetchall()]
    conn.close()

    articles = [_fmt_article(r) for r in rows]
    return render_template(
        'index.html',
        articles=articles,
        sources=sources,
        tab=tab,
        hours=hours,
        stats=stats,
    )


@app.route('/article/<int:article_id>')
def article(article_id: int):
    conn = _db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, title, link, summary, source, category,
               importance_score, hero_image, full_content, read_time, fetched_at
        FROM articles WHERE id = %s
    """, (article_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        abort(404)

    art = _fmt_article(row)
    art['full_content'] = row.get('full_content')

    # Related articles — same category, recent, different id
    cur.execute("""
        SELECT id, title, link, summary, source, category,
               importance_score, hero_image, read_time, fetched_at
        FROM articles
        WHERE category = %s AND id != %s
        ORDER BY fetched_at DESC
        LIMIT 4
    """, (art['category'], article_id))
    related = [_fmt_article(r) for r in cur.fetchall()]
    conn.close()

    return render_template('article.html', article=art, related=related)


@app.route('/api/articles')
def api_articles():
    tab   = request.args.get('tab', 'all')
    if tab not in ('all', 'tech', 'world', 'entertainment'):
        tab = 'all'
    hours = max(1, min(168, int(request.args.get('hours', 24))))
    interval = f'{hours} hours'

    conn = _db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if tab == 'all':
        where = "(category='tech' OR category='entertainment' OR importance_score >= 1)"
    elif tab == 'tech':
        where = "category='tech'"
    elif tab == 'entertainment':
        where = "category='entertainment'"
    else:
        where = "category='world' AND importance_score >= 1"

    cur.execute(f"""
        SELECT id, title, link, summary, source, category,
               importance_score, hero_image, read_time, fetched_at
        FROM articles
        WHERE {where}
          AND fetched_at >= NOW() - %s::interval
        ORDER BY
          CASE WHEN category='world' AND importance_score >= 2 THEN 0 ELSE 1 END,
          fetched_at DESC
        LIMIT 120
    """, (interval,))
    rows = cur.fetchall()
    conn.close()
    return jsonify([_fmt_article(r) for r in rows])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8009, debug=False)
