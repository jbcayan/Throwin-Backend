#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Wait for the PostgreSQL database to be ready
echo "Waiting for PostgreSQL to be available..."
while ! nc -z db 5432; do
  sleep 1
done

echo "PostgreSQL is up - continuing..."

# Navigate to the project directory where manage.py is located
cd /app/throwin


# Apply database migrations
echo "Applying migrations..."
python manage.py migrate

# Collect static files (optional, for production)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the Django development server
echo "Starting Django development server..."
python manage.py runserver 0.0.0.0:8000

# Start the Gunicorn server
#echo "Starting Gunicorn..."
#exec gunicorn throwin.wsgi:application --bind 0.0.0.0:8000
