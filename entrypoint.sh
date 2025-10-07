#!/bin/sh

set -e

# Run Alembic migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Start the application  
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload