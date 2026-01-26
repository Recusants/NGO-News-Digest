"""
Development settings.
"""
from .base import *

DEBUG = True

# Add localhost for development
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Use SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Disable security settings for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Email settings for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER = 'tinashemphisa45@gmail.com'
EMAIL_HOST_PASSWORD = 'ztej qsoa dngh zcgu'  #← Get from below
DEFAULT_FROM_EMAIL = 'tinashemphisa45@gmail.com'

# Additional development apps (like debug toolbar)
try:
    import django_extensions
    INSTALLED_APPS += ['django_extensions']
except ImportError:
    pass