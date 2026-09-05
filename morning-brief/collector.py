#!/usr/bin/env python3
"""
Tech Magazine — Collector v3
Fetches articles from RSS feeds and Hacker News API across tech domains:
  - AI & Machine Learning (ai_ml)
  - Robotics & Automation (robotics)
  - Autonomous Vehicles & Mobility (vehicles)
  - General Tech & Hardware (dev_hardware)
"""
import os
import re
import sys
from datetime import datetime

import feedparser
import requests
from db import get_conn, query, is_postgres

AI_SOURCES = [
    ('TechCrunch AI',      'rss', 'https://techcrunch.com/category/artificial-intelligence/feed/'),
    ('VentureBeat AI',     'rss', 'https://venturebeat.com/category/ai/feed/'),
    ('MIT Tech Review',    'rss', 'https://www.technologyreview.com/feed/'),
    ('Import AI',          'rss', 'https://importai.substack.com/feed'),
]

ROBOTICS_SOURCES = [
    ('IEEE Robotics',      'rss', 'https://spectrum.ieee.org/feeds/topic/robotics.rss'),
    ('TechCrunch Robotics','rss', 'https://techcrunch.com/category/robotics/feed/'),
    ('Robohub',            'rss', 'https://robohub.org/feed/'),
]

VEHICLES_SOURCES = [
    ('Electrek',           'rss', 'https://electrek.co/feed/'),
    ('Verge Mobility',     'rss', 'https://www.theverge.com/transportation/rss/index.xml'),
    ('InsideEVs',          'rss', 'https://insideevs.com/rss/articles/all/'),
    ('Ars Technica Cars',  'rss', 'https://feeds.arstechnica.com/arstechnica/technology-lab'),
]

DEV_HARDWARE_SOURCES = [
    ('The Verge',          'rss', 'https://www.theverge.com/rss/index.xml'),
    ('TechCrunch',         'rss', 'https://techcrunch.com/feed/'),
    ('Wired',              'rss', 'https://www.wired.com/feed/rss'),
    ('Ars Technica',       'rss', 'http://feeds.arstechnica.com/arstechnica/index'),
    ('Hacker News',        'hn',  None),
    ('Tom\'s Hardware',     'rss', 'https://www.tomshardware.com/feeds/all'),
    ('Engadget',           'rss', 'https://www.engadget.com/rss.xml'),
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

CRITICAL_TECH_KW = {
    'gpt','claude','gemini','openai','anthropic','llm','nvidia','robot','humanoid',
    'autonomous','waymo','tesla','quantum','chip','semiconductor','starship','spacex',
    'agent','supercomputer','cybersecurity','hack','vulnerability',
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
    conn = get_conn()
    added = 0
    for t, l, s, img in articles:
        cur = query(
            conn,
            """INSERT INTO articles (title, link, summary, source, category, subcategory, hero_image, enriched)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (link) DO NOTHING""",
            (t, l, s, source, category, category, img, img is not None)
        )
        added += (cur.rowcount if cur.rowcount > 0 else 0)
    conn.commit()
    conn.close()
    return added


# ── Fetchers ───────────────────────────────────────────────────────────────────
def _entry_image(entry) -> str | None:
    """Extract best image URL from a feedparser entry."""
    for mc in entry.get('media_content', []):
        url = mc.get('url', '')
        if url and any(url.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.webp')):
            return url
    for mt in entry.get('media_thumbnail', []):
        url = mt.get('url', '')
        if url:
            return url
    for enc in entry.get('enclosures', []):
        if enc.get('type', '').startswith('image/'):
            return enc.get('href') or enc.get('url')
    for link in entry.get('links', []):
        if link.get('type', '').startswith('image/'):
            return link.get('href')
    return None


def _fetch_rss(name: str, url: str, category: str) -> int:
    try:
        feed = feedparser.parse(url, request_headers=HEADERS)
        arts = []
        for e in feed.entries[:25]:
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
        print(f'  {name}: FAILED - {exc}', file=sys.stderr)
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
            summary  = f'{score} points · {comments} comments on Hacker News'
            arts.append((title, link, summary, None))
        added = _store('Hacker News', 'dev_hardware', arts)
        print(f'  Hacker News: {len(arts)} fetched, {added} new')
        return added
    except Exception as exc:
        print(f'  Hacker News: FAILED - {exc}', file=sys.stderr)
        return 0


# ── Importance Scoring ─────────────────────────────────────────────────────────
def _keywords(title: str) -> set[str]:
    words = re.findall(r'[a-z]{3,}', title.lower())
    return {w for w in words if w not in STOP_WORDS}


def _score_tech_articles():
    """Importance scoring for tech articles based on keyword popularity & critical terms."""
    try:
        conn = get_conn()
        cur  = query(conn, """
            SELECT id, title, source FROM articles
            WHERE fetched_at >= NOW() - INTERVAL '48 hours'
        """)
        rows = cur.fetchall()
        scores = {r[0]: 0 for r in rows}

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
                if overlap / smaller >= 0.35:
                    scores[id_a] = scores.get(id_a, 0) + 1
                    scores[id_b] = scores.get(id_b, 0) + 1

        for row_id, title, _ in rows:
            words = set(title.lower().split())
            if words & CRITICAL_TECH_KW:
                scores[row_id] = scores.get(row_id, 0) + 2

        for row_id, score in scores.items():
            if score > 0:
                query(conn,
                    'UPDATE articles SET importance_score = %s WHERE id = %s',
                    (score, row_id)
                )
        conn.commit()
        conn.close()
        scored = sum(1 for s in scores.values() if s > 0)
        print(f'  Tech scoring: {len(rows)} articles evaluated, {scored} scored')
    except Exception as exc:
        print(f'  Tech scoring FAILED - {exc}', file=sys.stderr)


def run_collector() -> int:
    print(f'[{datetime.now():%Y-%m-%d %H:%M:%S}] Tech Collector starting...', flush=True)
    total = 0

    print('-- AI & Machine Learning --', flush=True)
    for name, kind, url in AI_SOURCES:
        total += _fetch_rss(name, url, 'ai_ml')

    print('-- Robotics & Automation --', flush=True)
    for name, kind, url in ROBOTICS_SOURCES:
        total += _fetch_rss(name, url, 'robotics')

    print('-- EV & Mobility --', flush=True)
    for name, kind, url in VEHICLES_SOURCES:
        total += _fetch_rss(name, url, 'vehicles')

    print('-- General Tech & Dev --', flush=True)
    for name, kind, url in DEV_HARDWARE_SOURCES:
        if kind == 'hn':
            total += _fetch_hn()
        else:
            total += _fetch_rss(name, url, 'dev_hardware')

    print('-- Scoring --', flush=True)
    _score_tech_articles()

    print(f'[{datetime.now():%Y-%m-%d %H:%M:%S}] Done - {total} new articles stored.', flush=True)
    return total


if __name__ == '__main__':
    run_collector()
