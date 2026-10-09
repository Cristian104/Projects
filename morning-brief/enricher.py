#!/usr/bin/env python3
"""
Morning Brief — Content Enricher

Image strategy per article:
  1. Extract og:image / twitter:image from the article's own URL
  2. If none, find another article covering the same story (keyword overlap ≥ 40%)
     and try extracting OG image from that URL
  3. If still none, generate with Imagen 4 (google-genai)

Also extracts full article text via trafilatura and computes read time.
"""
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
import psycopg2.extras
import requests
import trafilatura

# ── Config ─────────────────────────────────────────────────────────────────────
DATABASE_URL   = os.getenv('DATABASE_URL', 'postgresql://admin:stacks_secure_pass_2024@stacks-postgres:5432/news')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyBuyHpi8lc7tpHwYOTpaeIB1JdMM1AZTFo')
GENERATED_DIR  = Path(__file__).parent / 'static' / 'generated'
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

DAILY_IMAGEN_LIMIT = 10  # max Imagen 4 calls per day to control API costs

CATEGORY_DEFAULTS = {
    'tech':          '/static/images/default-tech.png',
    'world':         '/static/images/default-world.png',
    'entertainment': '/static/images/default-entertainment.png',
}
DEFAULT_FALLBACK = '/static/images/default-world.png'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
    )
}

STOP_WORDS = {
    'the','a','an','and','or','but','in','on','at','to','for','of','with',
    'by','from','up','about','into','is','are','was','were','be','been',
    'have','has','had','do','does','did','will','would','could','should',
    'that','this','it','its','as','not','no','new','says','said','after',
    'over','more','than','just','all','also','back','out',
}


# ── Helpers ─────────────────────────────────────────────────────────────────────
def _title_keywords(title: str) -> set[str]:
    words = re.findall(r'[a-z]{3,}', title.lower())
    return {w for w in words if w not in STOP_WORDS}


def _fetch_og_image(url: str) -> str | None:
    """Extract og:image or twitter:image from a page's <head>."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        html = r.text
        for pat in [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](https?://[^"\']+)["\']',
            r'<meta[^>]+content=["\'](https?://[^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\'](https?://[^"\']+)["\']',
            r'<meta[^>]+content=["\'](https?://[^"\']+)["\'][^>]+name=["\']twitter:image["\']',
        ]:
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                return m.group(1).strip()
    except Exception:
        pass
    return None


def _cross_source_image(article_id: int, title: str, conn) -> str | None:
    """
    Find another article covering the same story and try extracting its OG image.
    Uses keyword overlap >= 40% of the smaller keyword set.
    """
    kw = _title_keywords(title)
    if not kw:
        return None

    cur = conn.cursor()
    cur.execute("""
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
                print(f'    ↳ cross-source image from article {row_id}')
                return img
    return None


def _get_today_imagen_count() -> int:
    """Count Imagen-generated images created today to enforce daily budget cap."""
    today = datetime.now().date()
    return sum(
        1 for f in GENERATED_DIR.glob('*.png')
        if datetime.fromtimestamp(f.stat().st_mtime).date() == today
    )


def _generate_image(title: str, article_id: int) -> str | None:
    """Generate a 16:9 hero image with Imagen via google-genai SDK. Tries Imagen 4 then 3."""
    if not GEMINI_API_KEY:
        return None
    try:
        import google.genai as genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = (
            f"Cinematic photorealistic news article hero image for the headline: '{title}'. "
            "Professional photojournalism style, dramatic lighting, wide format. "
            "No text overlay, no watermarks, no logos."
        )
        for model in ('imagen-4.0-generate-001', 'imagen-3.0-generate-001'):
            try:
                response = client.models.generate_images(
                    model=model,
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio='16:9',
                        output_mime_type='image/png',
                    ),
                )
                img_bytes = response.generated_images[0].image.image_bytes
                out_path  = GENERATED_DIR / f'{article_id}.png'
                out_path.write_bytes(img_bytes)
                print(f'    ↳ {model} generated')
                return f'/static/generated/{article_id}.png'
            except Exception as exc:
                print(f'    ↳ {model} failed: {exc}', file=sys.stderr)
        return None
    except Exception as exc:
        print(f'    ↳ Image generation failed: {exc}', file=sys.stderr)
        return None


def _extract_content(url: str) -> tuple[str | None, int]:
    """Extract main article body with trafilatura. Returns (text, read_time_minutes)."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None, 3
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if not text:
            return None, 3
        read_time = max(1, round(len(text.split()) / 200))
        return text, read_time
    except Exception:
        return None, 3


# ── Main batch ──────────────────────────────────────────────────────────────────
def enrich_batch(limit: int = 50):
    conn = psycopg2.connect(DATABASE_URL)
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    upd  = conn.cursor()

    cur.execute("""
        SELECT id, title, link, category, importance_score
        FROM articles
        WHERE enriched = FALSE
        ORDER BY
          CASE WHEN category = 'tech' THEN 0 ELSE 1 END,
          fetched_at DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    print(f'Enriching {len(rows)} articles…')

    imagen_used_today = _get_today_imagen_count()
    print(f'Imagen budget today: {imagen_used_today}/{DAILY_IMAGEN_LIMIT}')

    for row in rows:
        aid       = row['id']
        title     = row['title']
        url       = row['link']
        category  = row['category']
        importance = row['importance_score'] or 0

        print(f'  [{aid}] {title[:70]}')

        # ── Step 1: OG image from own URL ──
        hero_image = _fetch_og_image(url)
        if hero_image:
            print(f'    ↳ OG image found')

        # ── Step 2: Cross-source image ──
        if not hero_image:
            hero_image = _cross_source_image(aid, title, conn)

        # ── Step 3: Imagen generation (capped) or category default ──
        if not hero_image:
            if imagen_used_today < DAILY_IMAGEN_LIMIT:
                hero_image = _generate_image(title, aid)
                if hero_image:
                    imagen_used_today += 1
                    print(f'    ↳ Imagen used ({imagen_used_today}/{DAILY_IMAGEN_LIMIT} today)')
            else:
                hero_image = CATEGORY_DEFAULTS.get(category, DEFAULT_FALLBACK)
                print(f'    ↳ Daily Imagen limit reached — using default-{category}')

        # ── Full content + read time ──
        full_content, read_time = _extract_content(url)

        upd.execute("""
            UPDATE articles
            SET hero_image   = %s,
                full_content = %s,
                read_time    = %s,
                enriched     = TRUE
            WHERE id = %s
        """, (hero_image, full_content, read_time, aid))
        conn.commit()

        img_src = 'og' if hero_image and '/static/generated/' not in hero_image else \
                  'imagen4' if hero_image else 'none'
        print(f'    img={img_src} content={"yes" if full_content else "no"} rt={read_time}min')

    conn.close()
    print(f'Done — {len(rows)} articles enriched.')


if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    print(f'[{datetime.now():%Y-%m-%d %H:%M:%S}] Enricher starting…')
    enrich_batch(limit)
    print(f'[{datetime.now():%Y-%m-%d %H:%M:%S}] Enricher done.')
