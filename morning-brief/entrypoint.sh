#!/bin/sh
# On-Demand AI Curation Architecture

echo "[entrypoint] Generating dynamic version string..."
GIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "")
if [ -n "$GIT_HASH" ]; then
    echo "v5.3 ($GIT_HASH) • On-Demand" > version.txt
else
    echo "v5.3 (Top Progress Bar) • On-Demand" > version.txt
fi

echo "[entrypoint] Running DB migration..."
python db_migrate.py || echo "[entrypoint] Migration warning (continuing)"

echo "[entrypoint] Starting gunicorn..."
exec gunicorn app:app --bind 0.0.0.0:8009 --workers 2 --timeout 60
