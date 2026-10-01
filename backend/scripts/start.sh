#!/bin/sh
set -e
echo "Aplicando migrations..."
alembic upgrade head
echo "Rodando seed..."
python -m app.seed
echo "Subindo API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
