#!/bin/bash

set -e

cd /app/throwin

echo "Waiting for Redis..."
while ! nc -z redis_cache 6379; do
  sleep 1
done
echo "Redis is up!"

# Conditional migration logic
if [ "$DATABASE_TYPE" = "sqlite" ]; then
  if [ -f "/app/throwin/db.sqlite3" ]; then
    echo "SQLite DB already exists, skipping migrations..."
  else
    echo "No SQLite DB found, applying migrations..."
    python manage.py migrate --noinput
  fi
else
  echo "Applying migrations for non-SQLite DB..."
  python manage.py migrate --noinput
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear -v 2 || echo "Static files collection failed but continuing."

echo "Starting Celery worker..."
celery -A throwin worker --loglevel=info &

echo "Starting Celery beat..."
celery -A throwin beat --loglevel=info &

echo "Starting Gunicorn server..."
exec gunicorn throwin.wsgi:application --bind 0.0.0.0:8000