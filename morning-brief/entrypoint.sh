#!/bin/sh
# On-Demand AI Curation Architecture

echo "[entrypoint] Running DB migration..."
python db_migrate.py || echo "[entrypoint] Migration warning (continuing)"

echo "[entrypoint] Starting gunicorn..."
exec gunicorn app:app --bind 0.0.0.0:8009 --workers 2 --timeout 60
