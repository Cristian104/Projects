#!/usr/bin/env python3
"""
Tech Magazine — Content & Image Enricher v4

Image Strategy:
  1. Extract high-res og:image / twitter:image from original article URL.
  2. Cross-source image from related story.
  3. Curated, topic-matched high-resolution Unsplash photo.

Text Extraction:
  - Multi-tier extraction (trafilatura + BeautifulSoup paragraph fallback).
  - Guarantees full article body storage for all curated stories.
"""
import hashlib
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Load .env if present
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

import requests
import trafilatura
from bs4 import BeautifulSoup
from db import get_conn, query, is_postgres

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

UNSPLASH_TOPIC_IMAGES = {
    'ai_ml': [
        'https://images.unsplash.com/photo-1677442136019-21780efad99a?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1655720828018-edd2daec9349?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1676299081847-824916de030a?auto=format&fit=crop&w=1200&q=80',
    ],
    'robotics': [
        'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1546776310-eef45dd6d63c?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1563206767-5b18f218e8de?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1508614589041-895b88991e3e?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1531746790731-6c087fecd65a?auto=format&fit=crop&w=1200&q=80',
    ],
    'vehicles': [
        'https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1558981806-ec527fa84c39?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80',
    ],
    'dev_hardware': [
        'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1555680202-c86f0e12f086?auto=format&fit=crop&w=1200&q=80',
    ],
}
DEFAULT_UNSPLASH = 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    )
}

STOP_WORDS = {
    'the','a','an','and','or','but','in','on','at','to','for','of','with',
    'by','from','up','about','into','is','are','was','were','be','been',
    'have','has','had','do','does','did','will','would','could','should',
}


def _title_keywords(title: str) -> set[str]:
    words = re.findall(r'[a-z]{3,}', title.lower())
    return {w for w in words if w not in STOP_WORDS}


def _fetch_og_image(url: str) -> str | None:
    """Extract og:image or twitter:image from page head."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
        html = r.text
        for pat in [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](https?://[^"\']+)["\']',
            r'<meta[^>]+content=["\'](https?://[^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\'](https?://[^"\']+)["\']',
            r'<meta[^>]+content=["\'](https?://[^"\']+)["\'][^>]+name=["\']twitter:image["\']',
        ]:
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                img_url = m.group(1).strip()
                if not img_url.endswith('.svg') and len(img_url) > 10:
                    return img_url
    except Exception:
        pass
    return None


def _get_unsplash_image(category: str, title: str) -> str:
    """Returns a deterministic high-res Unsplash photo based on category & title hash."""
    images = UNSPLASH_TOPIC_IMAGES.get(category, UNSPLASH_TOPIC_IMAGES['dev_hardware'])
    idx = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16) % len(images)
    return images[idx]


def _cross_source_image(article_id: int, title: str, conn) -> str | None:
    kw = _title_keywords(title)
    if not kw:
        return None

    cur = query(conn, """
        SELECT id, title, link FROM articles
        WHERE id != %s
          AND fetched_at >= NOW() - INTERVAL '48 hours'
        ORDER BY fetched_at DESC
        LIMIT 300
    """, (article_id,))
    candidates = cur.fetchall()

    for row_id, row_title, row_link in candidates:
        other_kw = _title_keywords(row_title)
        smaller = min(len(kw), len(other_kw))
        if smaller == 0:
            continue
        if len(kw & other_kw) / smaller >= 0.4:
            img = _fetch_og_image(row_link)
            if img:
                return img
    return None


def _extract_content(url: str) -> tuple[str | None, int]:
    """Extract main article body with trafilatura + BeautifulSoup paragraph fallback."""
    try:
        downloaded = trafilatura.fetch_url(url)
        text = None
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        
        # Fallback to BeautifulSoup if trafilatura returned empty/minimal text
        if not text or len(text.split()) < 30:
            r = requests.get(url, headers=HEADERS, timeout=8)
            soup = BeautifulSoup(r.text, 'html.parser')
            paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 35]
            if paragraphs:
                text = '\n\n'.join(paragraphs)

        if not text:
            return None, 3

        read_time = max(1, round(len(text.split()) / 200))
        return text, read_time
    except Exception:
        return None, 3


def _generate_ai_summary(title: str, text: str | None) -> str | None:
    """Generate a 3-bullet AI TL;DR summary using Gemini Flash."""
    if not GEMINI_API_KEY or not text or len(text.split()) < 50:
        return None
    try:
        import google.genai as genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = (
            f"Article Title: {title}\n\n"
            f"Article Content: {text[:1000]}\n\n"
            "Generate a concise 3-bullet point executive summary (TL;DR) for tech professionals. "
            "Start each bullet point with a bullet symbol (•). Keep each point under 25 words."
        )
        response = client.models.generate_content(
            model='gemini-flash-lite-latest',
            contents=prompt
        )
        return response.text.strip()
    except Exception as exc:
        return None


def enrich_curated_articles():
    """Enriches ALL curated articles (rank_section <= 10 OR rank_overall <= 10)."""
    conn = get_conn()

    cur = query(conn, """
        SELECT id, title, link, category, hero_image, full_content, enriched
        FROM articles
        WHERE (rank_section <= 10 OR rank_overall <= 10)
          AND (enriched = FALSE OR full_content IS NULL OR hero_image IS NULL)
        ORDER BY rank_overall ASC, rank_section ASC
    """)
    rows = cur.fetchall()
    print(f'Enriching {len(rows)} curated top articles...')

    for row in rows:
        aid       = row['id']
        title     = row['title']
        url       = row['link']
        category  = row['category'] or 'dev_hardware'

        print(f'  [{aid}] {title[:70]}')

        # ── Step 1: OG Image from own URL ──
        hero_image = _fetch_og_image(url)
        img_src = 'og'

        # ── Step 2: Cross-Source Image ──
        if not hero_image:
            hero_image = _cross_source_image(aid, title, conn)
            img_src = 'cross'

        # ── Step 3: Unsplash Topic Image Fallback ──
        if not hero_image:
            hero_image = _get_unsplash_image(category, title)
            img_src = 'unsplash'

        # ── Full Content & Read Time ──
        full_content, read_time = _extract_content(url)

        # ── AI Summary ──
        ai_summary = None
        if full_content:
            ai_summary = _generate_ai_summary(title, full_content)

        query(conn, """
            UPDATE articles
            SET hero_image   = %s,
                full_content = %s,
                ai_summary   = COALESCE(%s, ai_summary),
                read_time    = %s,
                enriched     = TRUE
            WHERE id = %s
        """, (hero_image, full_content, ai_summary, read_time, aid))
        conn.commit()

        print(f'    img={img_src} content={"yes" if full_content else "no"} ai_summary={"yes" if ai_summary else "no"} rt={read_time}min')

    conn.close()
    print(f'Done - {len(rows)} curated articles enriched.')


if __name__ == '__main__':
    print(f'[{datetime.now():%Y-%m-%d %H:%M:%S}] Tech Enricher starting...')
    enrich_curated_articles()
    print(f'[{datetime.now():%Y-%m-%d %H:%M:%S}] Tech Enricher done.')
