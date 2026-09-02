"""Tech Intelligence Magazine — Flask Web App v4 (AI Curated & Impact Ranked). Port 8009."""
import html
import re

from flask import Flask, abort, jsonify, render_template, request
from db import get_conn, query, is_postgres

app = Flask(__name__)

VALID_TABS = {'all', 'ai_ml', 'robotics', 'vehicles', 'dev_hardware'}


# ── Helpers ────────────────────────────────────────────────────────────────────
def _clean_html(text: str, maxlen: int = 280) -> str:
    text = re.sub(r'<[^>]+>', '', text or '')
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return (text[:maxlen] + '…') if len(text) > maxlen else text


def _source_slug(name: str) -> str:
    return re.sub(r'[^a-z0-9]', '-', name.lower())


def _get_val(r, key, default=None):
    try:
        val = r[key]
        return val if val is not None else default
    except (KeyError, IndexError):
        return default


def _fmt_article(r) -> dict:
    fa = _get_val(r, 'fetched_at')
    return {
        'id':               _get_val(r, 'id'),
        'title':            _get_val(r, 'title'),
        'link':             _get_val(r, 'link'),
        'summary':          _clean_html(_get_val(r, 'summary'), 280),
        'source':           _get_val(r, 'source'),
        'source_slug':      _source_slug(_get_val(r, 'source') or ''),
        'category':         _get_val(r, 'category', 'dev_hardware'),
        'importance':       _get_val(r, 'importance_score', 0),
        'rank_section':     _get_val(r, 'rank_section', 99),
        'rank_overall':     _get_val(r, 'rank_overall', 99),
        'hero_image':       _get_val(r, 'hero_image'),
        'ai_summary':       _get_val(r, 'ai_summary'),
        'ai_impact_reason': _get_val(r, 'ai_impact_reason'),
        'read_time':        _get_val(r, 'read_time', 3),
        'fetched_at':       str(fa or '')[:16].replace('T', ' '),
    }


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    tab = request.args.get('tab', 'all')
    if tab not in VALID_TABS:
        tab = 'all'

    conn = get_conn()

    if tab == 'all':
        cur = query(conn, """
            SELECT id, title, link, summary, source, category,
                   importance_score, rank_section, rank_overall,
                   hero_image, ai_summary, ai_impact_reason, read_time, fetched_at
            FROM articles
            WHERE rank_overall <= 10
            ORDER BY rank_overall ASC
        """)
    else:
        cur = query(conn, """
            SELECT id, title, link, summary, source, category,
                   importance_score, rank_section, rank_overall,
                   hero_image, ai_summary, ai_impact_reason, read_time, fetched_at
            FROM articles
            WHERE category = %s AND rank_section <= 10
            ORDER BY rank_section ASC
        """, (tab,))

    rows = cur.fetchall()

    # Stats
    cur = query(conn, """
        SELECT
          (SELECT COUNT(*) FROM articles
           WHERE fetched_at >= NOW() - INTERVAL '24 hours') AS today,
          (SELECT COUNT(*) FROM articles
           WHERE category='ai_ml' AND fetched_at >= NOW() - INTERVAL '24 hours') AS ai_today,
          (SELECT COUNT(*) FROM articles) AS total,
          (SELECT MAX(fetched_at) FROM articles) AS last_fetch
    """)
    _sr    = cur.fetchone()
    stats  = dict(_sr) if _sr else {}
    if stats.get('last_fetch'):
        stats['last_fetch'] = str(stats['last_fetch'])[:16].replace('T', ' ')

    # Sources
    cur = query(conn, 'SELECT DISTINCT source FROM articles ORDER BY source')
    sources = [r['source'] for r in cur.fetchall()]
    conn.close()

    articles = [_fmt_article(r) for r in rows]
    return render_template(
        'index.html',
        articles=articles,
        sources=sources,
        tab=tab,
        stats=stats,
    )


@app.route('/article/<int:article_id>')
def article(article_id: int):
    conn = get_conn()
    cur = query(conn, """
        SELECT id, title, link, summary, source, category,
               importance_score, rank_section, rank_overall,
               hero_image, full_content, ai_summary, ai_impact_reason, read_time, fetched_at
        FROM articles WHERE id = %s
    """, (article_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        abort(404)

    art = _fmt_article(row)
    art['full_content'] = _get_val(row, 'full_content')

    # Related articles — same category, recent, different id
    cur = query(conn, """
        SELECT id, title, link, summary, source, category,
               importance_score, rank_section, rank_overall,
               hero_image, ai_summary, ai_impact_reason, read_time, fetched_at
        FROM articles
        WHERE category = %s AND id != %s
        ORDER BY rank_section ASC, fetched_at DESC
        LIMIT 4
    """, (art['category'], article_id))
    related = [_fmt_article(r) for r in cur.fetchall()]
    conn.close()

    return render_template('article.html', article=art, related=related)


@app.route('/api/articles')
def api_articles():
    tab = request.args.get('tab', 'all')
    if tab not in VALID_TABS:
        tab = 'all'

    conn = get_conn()

    if tab == 'all':
        cur = query(conn, """
            SELECT id, title, link, summary, source, category,
                   importance_score, rank_section, rank_overall,
                   hero_image, ai_summary, ai_impact_reason, read_time, fetched_at
            FROM articles
            WHERE rank_overall <= 10
            ORDER BY rank_overall ASC
        """)
    else:
        cur = query(conn, """
            SELECT id, title, link, summary, source, category,
                   importance_score, rank_section, rank_overall,
                   hero_image, ai_summary, ai_impact_reason, read_time, fetched_at
            FROM articles
            WHERE category = %s AND rank_section <= 10
            ORDER BY rank_section ASC
        """, (tab,))

    rows = cur.fetchall()
    conn.close()
    return jsonify([_fmt_article(r) for r in rows])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8009, debug=True)
