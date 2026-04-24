#!/usr/bin/env python3
"""
Morning Brief — Collector v2
Fetches articles from RSS feeds and Hacker News API, stores in PostgreSQL.
Assigns categories (tech/world) and scores world articles by cross-source importance.
Run hourly via cron.
"""
import os
import re
import sys
from datetime import datetime, timezone, timedelta

import feedparser
import psycopg2
import requests

# ── Config ─────────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://admin:stacks_secure_pass_2024@stacks-postgres:5432/news'
)

TECH_SOURCES = [
    ('The Verge',    'rss', 'https://www.theverge.com/rss/index.xml'),
    ('TechCrunch',   'rss', 'https://techcrunch.com/feed/'),
    ('Wired',        'rss', 'https://www.wired.com/feed/rss'),
    ('Ars Technica', 'rss', 'http://feeds.arstechnica.com/arstechnica/index'),
    ('Hacker News',  'hn',  None),
]
WORLD_SOURCES = [
    ('BBC World',  'rss', 'http://feeds.bbci.co.uk/news/world/rss.xml'),
    ('NYT World',  'rss', 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml'),
    ('Al Jazeera', 'rss', 'https://www.aljazeera.com/xml/rss/all.xml'),
]

ENTERTAINMENT_SOURCES = [
    ('Variety',              'rss', 'https://variety.com/feed/'),
    ('Hollywood Reporter',   'rss', 'https://www.hollywoodreporter.com/feed/'),
    ('Deadline',             'rss', 'https://deadline.com/feed/'),
    ('Collider',             'rss', 'https://collider.com/feed/'),
    ('Screen Rant',          'rss', 'https://screenrant.com/feed/'),
    ('The AV Club',          'rss', 'https://www.avclub.com/rss'),
]

HN_TOP  = 'https://hacker-news.firebaseio.com/v0/topstories.json'
HN_ITEM = 'https://hacker-news.firebaseio.com/v0/item/{}.json'

STOP_WORDS = {
    'the','a','an','and','or','but','in','on','at','to','for','of','with',
    'by','from','up','about','into','through','during','is','are','was',
    'were','be','been','being','have','has','had','do','does','did','will',
    'would','could','should','may','might','can','that','this','these',
    'those','it','its','as','not','no','new','says','said','after','over',
    'more','than','just','all','also','back','out','how','what','when',
    'who','why','where','he','she','they','we','you','your','our','their',
}

CATASTROPHIC_KW = {
    'war','killed','dead','deaths','arrested','earthquake','nuclear','collapse',
    'crash','attack','explosion','invasion','massacre','genocide','missile',
    'bomb','strike','sanctions',
}

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0 Safari/537.36'
    )
}


# ── DB helpers ─────────────────────────────────────────────────────────────────
def _store(source: str, category: str, articles: list[tuple]) -> int:
    """articles = list of (title, link, summary, hero_image_or_None)"""
    if not articles:
        return 0
    conn = psycopg2.connect(DATABASE_URL)
    cur  = conn.cursor()
    added = 0
    for t, l, s, img in articles:
        cur.execute(
            """INSERT INTO articles (title, link, summary, source, category, hero_image, enriched)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (link) DO NOTHING""",
            (t, l, s, source, category, img, img is not None)
        )
        added += cur.rowcount
    conn.commit()
    conn.close()
    return added


# ── Fetchers ───────────────────────────────────────────────────────────────────
def _entry_image(entry) -> str | None:
    """Extract best image URL from a feedparser entry."""
    # media:content (common in Verge, Ars, Al Jazeera)
    for mc in entry.get('media_content', []):
        url = mc.get('url', '')
        if url and any(url.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.webp')):
            return url
    # media:thumbnail (BBC, Reuters)
    for mt in entry.get('media_thumbnail', []):
        url = mt.get('url', '')
        if url:
            return url
    # enclosures (some feeds)
    for enc in entry.get('enclosures', []):
        if enc.get('type', '').startswith('image/'):
            return enc.get('href') or enc.get('url')
    # links with image type
    for link in entry.get('links', []):
        if link.get('type', '').startswith('image/'):
            return link.get('href')
    return None


def _fetch_rss(name: str, url: str, category: str) -> int:
    try:
        feed = feedparser.parse(url, request_headers=HEADERS)
        arts = []
        for e in feed.entries[:30]:
            title   = (e.get('title') or '').strip()
            link    = (e.get('link')  or '').strip()
            summary = (e.get('summary') or e.get('description') or '').strip()
            img     = _entry_image(e)
            if title and link:
                arts.append((title, link, summary, img))
        added = _store(name, category, arts)
        imgs  = sum(1 for _, _, _, i in arts if i)
        print(f'  {name}: {len(arts)} fetched, {added} new, {imgs} with image')
        return added
    except Exception as exc:
        print(f'  {name}: FAILED — {exc}', file=sys.stderr)
        return 0


def _fetch_hn(limit: int = 25) -> int:
    try:
        ids  = requests.get(HN_TOP, timeout=10).json()
        arts = []
        for story_id in ids[:limit]:
            item = requests.get(HN_ITEM.format(story_id), timeout=5).json()
            if not item or item.get('type') == 'job':
                continue
            title    = item.get('title', 'No Title')
            link     = item.get('url') or f'https://news.ycombinator.com/item?id={story_id}'
            score    = item.get('score', 0)
            comments = item.get('descendants', 0)
            summary  = f'{score} points · {comments} comments on HN'
            arts.append((title, link, summary, None))  # HN has no images in API
        added = _store('Hacker News', 'tech', arts)
        print(f'  Hacker News: {len(arts)} fetched, {added} new')
        return added
    except Exception as exc:
        print(f'  Hacker News: FAILED — {exc}', file=sys.stderr)
        return 0


# ── Importance scoring ─────────────────────────────────────────────────────────
def _keywords(title: str) -> set[str]:
    words = re.findall(r'[a-z]{3,}', title.lower())
    return {w for w in words if w not in STOP_WORDS}


def _score_world_articles():
    """Cross-source importance scoring for world articles from the last 48 hours."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, title, source FROM articles
            WHERE category = 'world'
              AND fetched_at >= NOW() - INTERVAL '48 hours'
        """)
        rows = cur.fetchall()
        scores = {r[0]: 0 for r in rows}

        # Cross-source keyword overlap
        for i, (id_a, title_a, src_a) in enumerate(rows):
            kw_a = _keywords(title_a)
            for id_b, title_b, src_b in rows[i+1:]:
                if src_a == src_b:
                    continue
                kw_b = _keywords(title_b)
                smaller = min(len(kw_a), len(kw_b))
                if smaller == 0:
                    continue
                overlap = len(kw_a & kw_b)
                if overlap / smaller >= 0.4:
                    scores[id_a] = scores.get(id_a, 0) + 1
                    scores[id_b] = scores.get(id_b, 0) + 1

        # Catastrophic keyword bonus
        for row_id, title, _ in rows:
            words = set(title.lower().split())
            if words & CATASTROPHIC_KW:
                scores[row_id] = scores.get(row_id, 0) + 2

        # Apply scores
        for row_id, score in scores.items():
            if score > 0:
                cur.execute(
                    'UPDATE articles SET importance_score = %s WHERE id = %s',
                    (score, row_id)
                )
        conn.commit()
        conn.close()
        scored = sum(1 for s in scores.values() if s > 0)
        print(f'  World scoring: {len(rows)} articles evaluated, {scored} scored')
    except Exception as exc:
        print(f'  World scoring FAILED — {exc}', file=sys.stderr)


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print(f'[{datetime.now():%Y-%m-%d %H:%M:%S}] Collector v2 starting…')
    total = 0

    print('── Tech sources ──')
    for name, kind, url in TECH_SOURCES:
        if kind == 'hn':
            total += _fetch_hn()
        else:
            total += _fetch_rss(name, url, 'tech')

    print('── World sources ──')
    for name, kind, url in WORLD_SOURCES:
        total += _fetch_rss(name, url, 'world')

    print('── Entertainment sources ──')
    for name, kind, url in ENTERTAINMENT_SOURCES:
        total += _fetch_rss(name, url, 'entertainment')

    print('── Scoring ──')
    _score_world_articles()

    print(f'[{datetime.now():%Y-%m-%d %H:%M:%S}] Done — {total} new articles stored.')
