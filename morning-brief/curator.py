"""
Morning Brief — AI Curation & Impact Ranking Engine v5
Uses Gemini Flash Lite to deduplicate candidate stories, select Top 10 per category,
rank them by impact, and produce AI impact summaries.
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


def curate_category(category: str):
    """Curates candidate articles for a category and assigns rank_section (1..10)."""
    conn = get_conn()

    cur = query(conn, """
        SELECT id, title, summary, source, link, fetched_at
        FROM articles
        WHERE category = %s
        ORDER BY fetched_at DESC
        LIMIT 50
    """, (category,))
    candidates = cur.fetchall()

    if not candidates or len(candidates) < 3:
        print(f"  [{category}] Insufficient candidate articles ({len(candidates)} found). Skipping curation.")
        conn.close()
        return

    items_text = []
    for c in candidates:
        aid = c['id']
        t = c['title']
        s = (c['summary'] or '')[:200].replace('\n', ' ')
        items_text.append(f"ID: {aid} | Title: {t} | Summary: {s}")

    candidates_block = "\n".join(items_text)

    prompt = f"""You are the Executive Tech Editor for Tech Pulse Magazine.
Review these {len(candidates)} recent raw tech articles from the '{category}' domain:

{candidates_block}

Task:
1. Select the 10 MOST impactful, innovative, and important articles for tech professionals to read.
2. Remove duplicate or near-identical stories (keep the single best source).
3. Rank the top 10 articles strictly from #1 (most important/groundbreaking) to #10.
4. For each selected article, provide a 1-sentence 'impact_reason' explaining WHY this story matters.

Return ONLY a valid JSON array of objects with keys: "id" (number), "rank" (number 1..10), "impact_reason" (string).
JSON Output:"""

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

        # Reset category ranks
        query(conn, "UPDATE articles SET rank_section = 99 WHERE category = %s", (category,))
        conn.commit()

        # Apply section ranks
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
        print(f"  [{category}] Successfully curated and ranked Top {len(ranked_items)} articles.", flush=True)
    except Exception as exc:
        print(f"  [{category}] AI Curation Failed: {exc}", file=sys.stderr, flush=True)
    finally:
        conn.close()


def curate_master_all():
    """Selects and ranks Top 10 Overall Tech Headlines across all categories."""
    conn = get_conn()

    cur = query(conn, """
        SELECT id, title, summary, source, category, rank_section, ai_impact_reason
        FROM articles
        WHERE rank_section <= 10
        ORDER BY rank_section ASC
    """)
    candidates = cur.fetchall()

    if not candidates:
        print("  [all] No section-curated articles found. Skipping master curation.")
        conn.close()
        return

    items_text = []
    for c in candidates:
        aid = c['id']
        t = c['title']
        cat = c['category']
        rsn = c.get('ai_impact_reason') or (c['summary'] or '')[:160]
        items_text.append(f"ID: {aid} | Category: {cat} | Title: {t} | Reason: {rsn}")

    candidates_block = "\n".join(items_text)

    prompt = f"""You are the Editor-in-Chief of Tech Pulse Magazine.
Here are 40 top section-curated headlines across AI, Robotics, Mobility, and Hardware:

{candidates_block}

Task:
1. Select the absolute Top 10 Headlines overall that are the most urgent, groundbreaking, and important across ALL tech fields today.
2. Rank them strictly 1 to 10.
3. Keep or refine the 1-sentence 'impact_reason'.

Return ONLY a valid JSON array of objects with keys: "id" (number), "rank" (number 1..10), "impact_reason" (string).
JSON Output:"""

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
    conn = get_conn()
    try:
        query(conn, "UPDATE curation_meta SET is_curating = TRUE WHERE id = 1")
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

    for cat in CATEGORIES:
        curate_category(cat)

    print("  Running Master Curation for 'all' tab...", flush=True)
    curate_master_all()

    print("  Enriching full text & images for all curated top stories...", flush=True)
    enrich_curated_articles()

    # Finalize curation metadata & update timestamps
    conn = get_conn()
    try:
        now_sql = "CURRENT_TIMESTAMP" if not is_postgres() else "NOW()"
        query(conn, f"UPDATE curation_meta SET is_curating = FALSE, last_curated_at = {now_sql} WHERE id = 1")
        query(conn, f"UPDATE articles SET fetched_at = {now_sql} WHERE rank_section <= 10 OR rank_overall <= 10")
        conn.commit()
    except Exception as exc:
        print(f"Error finalizing curation meta: {exc}", file=sys.stderr)
    finally:
        conn.close()

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] AI Curation & Enrichment complete.", flush=True)


if __name__ == '__main__':
    run_full_curation()
