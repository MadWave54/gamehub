#!/bin/sh
# Подготовка контейнера backend: миграции, статика, справочник игр.
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
mkdir -p /backend_static/static && cp -r /app/collected_static/. /backend_static/static/ 2>/dev/null || true
if [ -f /app/data/games.json ]; then python manage.py load_data --path /app/data/games.json; fi
exec "$@"
