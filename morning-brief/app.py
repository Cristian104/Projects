"""Tech Intelligence Magazine — Flask Web App v5.1 (Real-Time AI Curation). Port 8009."""
import html
import os
import re
import subprocess
import sys
import threading
from datetime import datetime, timezone

from flask import Flask, abort, jsonify, render_template, request
from db import get_conn, query, is_postgres

app = Flask(__name__)

VALID_TABS = {'all', 'ai_ml', 'robotics', 'vehicles', 'dev_hardware'}

IS_CURATING = False
CURATION_LOCK = threading.Lock()


# ── Version Management ────────────────────────────────────────────────────────
def get_app_version() -> str:
    """Returns dynamic version string from version.txt or git rev-parse."""
    version_file = os.path.join(os.path.dirname(__file__), 'version.txt')
    if os.path.exists(version_file):
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                v = f.read().strip()
                if v:
                    return v
        except Exception:
            pass
    try:
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True).strip()
        return f"v5.1 ({commit}) • On-Demand"
    except Exception:
        return "v5.1-lite • On-Demand"


@app.context_processor
def inject_global_vars():
    return dict(app_version=get_app_version())


# ── Background Curation Spawner ────────────────────────────────────────────────
def _run_bg_curation():
    global IS_CURATING
    with CURATION_LOCK:
        if IS_CURATING:
            return
        IS_CURATING = True

    conn = get_conn()
    try:
        query(conn, "UPDATE curation_meta SET is_curating = TRUE WHERE id = 1")
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

    try:
        print("[On-Demand Curation] Starting background collector & curator...")
        from collector import run_collector
        from curator import run_full_curation

        run_collector()
        run_full_curation()
        print("[On-Demand Curation] Curation complete.")
    except Exception as exc:
        print(f"[On-Demand Curation] Error: {exc}", file=sys.stderr)
        conn = get_conn()
        try:
            query(conn, "UPDATE curation_meta SET is_curating = FALSE WHERE id = 1")
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()
    finally:
        with CURATION_LOCK:
            IS_CURATING = False


def _check_stale_and_trigger(conn):
    """Spawns curation if top curated articles are older than 4 hours."""
    global IS_CURATING
    if IS_CURATING:
        return True

    try:
        cur = query(conn, "SELECT last_curated_at, is_curating FROM curation_meta WHERE id = 1")
        row = cur.fetchone()
        
        last = row['last_curated_at'] if row else None
        db_curating = row['is_curating'] if row else False

        if db_curating:
            IS_CURATING = True
            return True

        should_curate = False
        if not last:
            should_curate = True
        else:
            if isinstance(last, str):
                try:
                    last_dt = datetime.fromisoformat(last)
                except Exception:
                    last_dt = datetime.now()
            else:
                last_dt = last

            now = datetime.now(last_dt.tzinfo) if getattr(last_dt, 'tzinfo', None) else datetime.now()
            age_hours = (now - last_dt).total_seconds() / 3600.0
            if age_hours >= 12.0:
                should_curate = True

        if should_curate:
            t = threading.Thread(target=_run_bg_curation, daemon=True)
            t.start()
            return True
    except Exception as exc:
        print(f"Stale check error: {exc}", file=sys.stderr)

    return IS_CURATING


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

    # Trigger background curation if cache is stale (>12h)
    is_updating = _check_stale_and_trigger(conn)

    if tab == 'all':
        cur = query(conn, """
            SELECT id, title, link, summary, source, category,
                   importance_score, rank_section, rank_overall,
                   hero_image, ai_summary, ai_impact_reason, read_time, fetched_at
            FROM articles
            WHERE rank_overall <= 10
            ORDER BY rank_overall ASC
        """)
        rows = cur.fetchall()
        if not rows:
            cur = query(conn, """
                SELECT id, title, link, summary, source, category,
                       importance_score, rank_section, rank_overall,
                       hero_image, ai_summary, ai_impact_reason, read_time, fetched_at
                FROM articles
                ORDER BY fetched_at DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
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
        if not rows:
            cur = query(conn, """
                SELECT id, title, link, summary, source, category,
                       importance_score, rank_section, rank_overall,
                       hero_image, ai_summary, ai_impact_reason, read_time, fetched_at
                FROM articles
                WHERE category = %s
                ORDER BY fetched_at DESC
                LIMIT 10
            """, (tab,))
            rows = cur.fetchall()

    # Stats
    cur = query(conn, """
        SELECT
          (SELECT COUNT(*) FROM articles) AS total,
          (SELECT MAX(fetched_at) FROM articles WHERE rank_section <= 10) AS last_fetch
    """)
    _sr    = cur.fetchone()
    stats  = dict(_sr) if _sr else {}
    if stats.get('last_fetch'):
        stats['last_fetch'] = str(stats['last_fetch'])[:16].replace('T', ' ')

    conn.close()

    articles = [_fmt_article(r) for r in rows]
    return render_template(
        'index.html',
        articles=articles,
        tab=tab,
        stats=stats,
        is_updating=is_updating,
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

    # Related articles
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


@app.route('/api/curate-status')
def api_curate_status():
    """Returns live AI curation status."""
    conn = get_conn()
    try:
        cur = query(conn, "SELECT is_curating, last_curated_at FROM curation_meta WHERE id = 1")
        row = cur.fetchone()
        db_curating = row['is_curating'] if row else False
        last_at = str(row['last_curated_at'])[:16].replace('T', ' ') if row and row['last_curated_at'] else ''
    except Exception:
        db_curating = False
        last_at = ''
    finally:
        conn.close()

    return jsonify({
        'is_curating': IS_CURATING or db_curating,
        'last_curated_at': last_at,
        'version': get_app_version()
    })


@app.route('/api/curate-now', methods=['GET', 'POST'])
def api_curate_now():
    """Explicitly triggers fresh AI Curation."""
    t = threading.Thread(target=_run_bg_curation, daemon=True)
    t.start()
    return jsonify({
        'ok': True,
        'status': 'curating'
    })


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
