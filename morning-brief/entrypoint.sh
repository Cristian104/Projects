#!/bin/sh
# No set -e — failures must not block gunicorn

echo "[entrypoint] Running DB migration..."
python db_migrate.py || echo "[entrypoint] Migration warning (continuing)"

echo "[entrypoint] Running initial collector..."
python collector.py || echo "[entrypoint] Collector warning (continuing)"

echo "[entrypoint] Running AI curator & enricher..."
python curator.py || echo "[entrypoint] Curator warning (continuing)"

echo "[entrypoint] Starting 2-hour AI curation loop in background..."
(while true; do
    sleep 7200
    echo "[cron] Running 2-hour collector & AI curator..."
    python collector.py
    python curator.py
done) &

echo "[entrypoint] Starting gunicorn..."
exec gunicorn app:app --bind 0.0.0.0:8009 --workers 2 --timeout 60
