#!/bin/sh
# No set -e — failures must not block gunicorn

echo "[entrypoint] Running DB migration..."
python db_migrate.py || echo "[entrypoint] Migration warning (continuing)"

echo "[entrypoint] Running initial collector..."
python collector.py || echo "[entrypoint] Collector warning (continuing)"

echo "[entrypoint] Starting enricher loop in background..."
(while true; do
    python enricher.py 50
    sleep 600  # re-enrich every 10 minutes for new articles
done) &

echo "[entrypoint] Starting hourly collector loop in background..."
(while true; do sleep 3600; echo "[cron] Running collector..."; python collector.py; done) &

echo "[entrypoint] Starting gunicorn..."
exec gunicorn app:app --bind 0.0.0.0:8009 --workers 2 --timeout 60
