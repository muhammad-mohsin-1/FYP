#!/bin/sh
# Railway entrypoint: seed the database, then serve backend + frontend on $PORT
set -e
echo "Seeding database..."
python -m backend.seed || true
echo "Starting server on port ${PORT:-8000}..."
exec uvicorn demo_server:app --host 0.0.0.0 --port "${PORT:-8000}"
