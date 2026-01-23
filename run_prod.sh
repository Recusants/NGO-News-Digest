#!/bin/bash
export DJANGO_ENV=production
export DEBUG=False
export DATABASE_URL=postgres://user:pass@localhost/dbname
python manage.py collectstatic --noinput
gunicorn newsletter.wsgi:application