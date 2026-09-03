#!/usr/bin/env python3
"""
Tech Magazine — AI Curator & Impact Ranking Engine v1
Uses Gemini AI (gemini-flash-latest) to filter candidate feed items,
remove duplicates, select the Top 10 articles per domain, rank them 1..10,
and perform a Master Curation for the Top 10 Overall Tech Headlines.
"""
import json
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

import google.genai as genai
from db import get_conn, query, is_postgres

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
CATEGORIES = ['ai_ml', 'robotics', 'vehicles', 'dev_hardware']


def get_ai_client():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
    return genai.Client(api_key=GEMINI_API_KEY)


def curate_category(category: str, limit_candidates: int = 50):
    """
    Selects and ranks Top 10 articles for a single category using Gemini AI.
    """
    conn = get_conn()
    cur = query(conn, """
        SELECT id, title, summary, source FROM articles
        WHERE category = %s
          AND fetched_at >= NOW() - INTERVAL '72 hours'
        ORDER BY fetched_at DESC
        LIMIT %s
    """, (category, limit_candidates))
    rows = cur.fetchall()

    if not rows:
        print(f"  [{category}] No candidate articles found.")
        conn.close()
        return

    articles_payload = []
    for r in rows:
        articles_payload.append({
            "id": r['id'],
            "title": r['title'],
            "summary": (r['summary'] or '')[:180],
            "source": r['source']
        })

    prompt = f"""
You are an expert Chief Technology Editor curating a top-tier tech magazine for category '{category}'.

Candidate Articles (Total {len(articles_payload)}):
{json.dumps(articles_payload, indent=2)}

Task:
1. Filter out duplicate stories covering the same underlying news event.
2. Select the top 10 MOST impactful, educational, and relevant articles for tech professionals.
3. Sort them from Rank #1 (Highest Global Impact / Must-Read Headline) down to Rank #10.
4. For each selected article, provide a 1-sentence "impact_reason" explaining why it matters and what the reader learns.

Return ONLY a valid JSON array of objects with this structure:
[
  {{
    "id": <article_id_int>,
    "rank": <int_1_to_10>,
    "impact_reason": "<1-sentence impact explanation>"
  }}
]
"""

    client = get_ai_client()
    try:
        response = client.models.generate_content(
            model='gemini-flash-lite-latest',
            contents=prompt
        )
        raw_text = response.text.strip()
        # Clean JSON markdown fences if present
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?", "", raw_text)
            raw_text = re.sub(r"```$", "", raw_text).strip()

        ranked_items = json.loads(raw_text)

        # Reset existing ranks for this category
        query(conn, "UPDATE articles SET rank_section = 99 WHERE category = %s", (category,))
        conn.commit()

        # Apply new ranks
        for item in ranked_items:
            aid = item["id"]
            rnk = item["rank"]
            rsn = item.get("impact_reason", "")
            query(conn, """
                UPDATE articles
                SET rank_section = %s,
                    ai_impact_reason = %s
                WHERE id = %s
            """, (rnk, rsn, aid))
        conn.commit()
        print(f"  [{category}] Successfully curated and ranked Top {len(ranked_items)} articles.")
    except Exception as exc:
        print(f"  [{category}] AI Curation Failed: {exc}", file=sys.stderr)
    finally:
        conn.close()


def curate_master_all():
    """
    Selects and ranks Top 10 Overall Tech Headlines across all categories.
    """
    conn = get_conn()
    cur = query(conn, """
        SELECT id, title, summary, source, category FROM articles
        WHERE rank_section <= 10
        ORDER BY fetched_at DESC
        LIMIT 40
    """)
    rows = cur.fetchall()

    if not rows:
        print("  [all] No section-curated articles available.")
        conn.close()
        return

    articles_payload = []
    for r in rows:
        articles_payload.append({
            "id": r['id'],
            "title": r['title'],
            "summary": (r['summary'] or '')[:180],
            "source": r['source'],
            "category": r['category']
        })

    prompt = f"""
You are the Master Editor-in-Chief of a global technology magazine.

Top Curated Stories Across All Domains (Total {len(articles_payload)}):
{json.dumps(articles_payload, indent=2)}

Task:
1. Evaluate all candidates across AI, Robotics, EV/Mobility, and Hardware/Dev.
2. Select the Top 10 Overall Tech Headlines globally.
3. Sort them from Rank #1 (The Single Most Important Tech News Globally Today) down to Rank #10.
4. Ensure balanced representation across major breakthroughs.

Return ONLY a valid JSON array of objects with this structure:
[
  {{
    "id": <article_id_int>,
    "rank": <int_1_to_10>,
    "impact_reason": "<1-sentence global impact summary>"
  }}
]
"""

    client = get_ai_client()
    try:
        response = client.models.generate_content(
            model='gemini-flash-lite-latest',
            contents=prompt
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?", "", raw_text)
            raw_text = re.sub(r"```$", "", raw_text).strip()

        ranked_items = json.loads(raw_text)

        # Reset overall ranks
        query(conn, "UPDATE articles SET rank_overall = 99")
        conn.commit()

        # Apply master overall ranks
        for item in ranked_items:
            aid = item["id"]
            rnk = item["rank"]
            rsn = item.get("impact_reason", "")
            query(conn, """
                UPDATE articles
                SET rank_overall = %s,
                    ai_impact_reason = %s
                WHERE id = %s
            """, (rnk, rsn, aid))
        conn.commit()
        print(f"  [all] Master Curation Complete: Top {len(ranked_items)} Overall Stories Ranked.", flush=True)
    except Exception as exc:
        print(f"  [all] Master AI Curation Failed: {exc}", file=sys.stderr, flush=True)
    finally:
        conn.close()


from enricher import enrich_curated_articles

def run_full_curation():
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] AI Curation & Impact Ranking starting...", flush=True)
    for cat in CATEGORIES:
        curate_category(cat)
    print("  Running Master Curation for 'all' tab...", flush=True)
    curate_master_all()
    print("  Enriching full text & images for all curated top stories...", flush=True)
    enrich_curated_articles()
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] AI Curation & Enrichment complete.", flush=True)


if __name__ == '__main__':
    run_full_curation()
