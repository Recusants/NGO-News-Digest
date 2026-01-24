#!/bin/bash
# start.sh - Startup script for Railway

echo "🚀 Starting Django application..."

# Run migrations
echo "📦 Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "🌐 Starting Gunicorn..."
exec gunicorn newsletter.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --worker-class gthread \
    --threads 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -