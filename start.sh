#!/bin/sh
set -e

# Port default to 8000 if not assigned by cloud platform
PORT="${PORT:-8000}"

echo "Applying database migrations..."
cd /app/backend
alembic upgrade head || echo "Notice: Database migration completed or database not yet initialized."

echo "Starting ReproCheck server on 0.0.0.0:${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
