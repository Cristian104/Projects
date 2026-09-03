#!/bin/sh
# No set -e — failures must not block gunicorn

echo "[entrypoint] Running DB migration..."
python db_migrate.py || echo "[entrypoint] Migration warning (continuing)"

echo "[entrypoint] Launching initial collector & AI curator in background..."
(
    python collector.py
    python curator.py
) &

echo "[entrypoint] Starting 4-hour AI curation loop in background..."
(while true; do
    sleep 14400
    echo "[cron] Running 4-hour collector & AI curator..."
    python collector.py
    python curator.py
done) &

echo "[entrypoint] Starting gunicorn immediately..."
exec gunicorn app:app --bind 0.0.0.0:8009 --workers 2 --timeout 60
