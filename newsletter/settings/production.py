"""
Production settings for cPanel deployment with MySQL
"""
from .base import *
import os


# ==============================================================================
# CRITICAL: These MUST be set in cPanel Environment Variables
# ==============================================================================

# # Security - MUST be set in cPanel
# SECRET_KEY = os.environ.get('SECRET_KEY')
# if not SECRET_KEY:
#     raise ValueError("❌ SECRET_KEY environment variable not set in cPanel!")

# # Debug must be False in production
# DEBUG = False

# # Allowed hosts - MUST be set in cPanel (comma-separated)
# ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
# if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
#     raise ValueError("❌ ALLOWED_HOSTS environment variable not set in cPanel!")


import logging

DEBUG = True
# Log all errors to a file
logging.basicConfig(
    filename='/home/ngodiges/django_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s'
)



# ==============================================================================
# Database - MySQL using PyMySQL
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

if not DATABASES['default']['NAME']:
    raise ValueError("❌ Database NAME not configured! Set DB_NAME in cPanel.")


# ==============================================================================
# Email - Optional, but needed for your app
# ==============================================================================
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ==============================================================================
# Security Settings for cPanel
# ==============================================================================
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSRF Trust - Add your domain
CSRF_TRUSTED_ORIGINS = [f'https://{host}' for host in ALLOWED_HOSTS if host]

# ==============================================================================
# Static Files
# ==============================================================================
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==============================================================================
# MySQL-specific settings
# ==============================================================================
# If you're using MySQL 5.7+ with JSON support, you can use JSONField
# Otherwise, Django will use TextField for JSON
if 'django.contrib.postgres' in INSTALLED_APPS:
    INSTALLED_APPS.remove('django.contrib.postgres')