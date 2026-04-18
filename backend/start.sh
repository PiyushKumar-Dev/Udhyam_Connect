#!/bin/sh
set -e
alembic upgrade head
python data/seed.py
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
