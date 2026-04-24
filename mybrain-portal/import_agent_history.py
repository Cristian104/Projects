"""
Import existing OpenClaw session history into the AgentMessage DB table.
Run once on VPS: python3 import_agent_history.py
"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "instance" / "db.sqlite"
SESSIONS_BASE = Path("/home/jorg/stacks/openclaw2/agents")

AGENT_MAP = {
    "main": "main",
    "peccata": "peccata",
    "argos": "argos",
    "mundi": "mundi",
}


def extract_text(content) -> str:
    """Extract plain text from OpenClaw message content (string or block list)."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts).strip()
    return ""


def import_session(cursor, jsonl_path: Path, agent_id: str, dry_run=False):
    imported = 0
    skipped = 0

    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("type") != "message":
                continue

            msg = event.get("message", {})
            role_raw = msg.get("role", "")
            if role_raw not in ("user", "assistant"):
                continue

            role = "agent" if role_raw == "assistant" else "user"
            text = extract_text(msg.get("content", ""))
            if not text:
                skipped += 1
                continue

            ts_str = event.get("timestamp") or msg.get("timestamp")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    ts = ts.replace(tzinfo=None)  # store as naive UTC
                except Exception:
                    ts = datetime.utcnow()
            else:
                ts = datetime.utcnow()

            if not dry_run:
                cursor.execute(
                    """INSERT INTO agent_message (agent_id, role, source, content, timestamp, user_id)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (agent_id, role, "telegram", text, ts.isoformat(), None),
                )
            imported += 1

    return imported, skipped


def main(dry_run=False):
    if not DB_PATH.exists():
        print(f"ERROR: DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_message (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id VARCHAR(30) NOT NULL,
            role VARCHAR(10) NOT NULL,
            source VARCHAR(20) DEFAULT 'web',
            content TEXT NOT NULL,
            timestamp DATETIME,
            user_id INTEGER
        )
    """)

    # Check what's already imported to avoid duplicates
    cursor.execute("SELECT COUNT(*) FROM agent_message WHERE source='telegram'")
    existing = cursor.fetchone()[0]
    if existing > 0 and not dry_run:
        print(f"Found {existing} existing telegram messages. Skipping already-imported entries is NOT checked — run with --dry-run first.")

    total_imported = 0

    for agent_dir_name, agent_id in AGENT_MAP.items():
        sessions_dir = SESSIONS_BASE / agent_dir_name / "sessions"
        if not sessions_dir.exists():
            continue

        for jsonl_file in sessions_dir.glob("*.jsonl"):
            print(f"  Processing {agent_dir_name}/{jsonl_file.name} ...")
            n, skipped = import_session(cursor, jsonl_file, agent_id, dry_run)
            print(f"    → {n} messages imported, {skipped} skipped")
            total_imported += n

    if not dry_run:
        conn.commit()
        print(f"\n✅ Done. {total_imported} messages imported into agent_message table.")
    else:
        print(f"\n[DRY RUN] Would import {total_imported} messages.")

    conn.close()


if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("=== DRY RUN — no changes will be made ===\n")
    main(dry_run=dry_run)
