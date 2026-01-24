"""
Production settings for Railway deployment
"""
from .base import *
import os

# Override base settings for production
DEBUG = True

# CRITICAL: Railway domain settings
# Get domain from environment or use wildcards
RAILWAY_PUBLIC_DOMAIN = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '')
RAILWAY_STATIC_URL = os.environ.get('RAILWAY_STATIC_URL', '')

# Build ALLOWED_HOSTS dynamically
ALLOWED_HOSTS = []

# Add Railway domains
if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)
    # Also add without port if present
    if ':' in RAILWAY_PUBLIC_DOMAIN:
        ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN.split(':')[0])

if RAILWAY_STATIC_URL:
    ALLOWED_HOSTS.append(RAILWAY_STATIC_URL)

# Add common Railway patterns
ALLOWED_HOSTS.extend([
    '.railway.app',
    '.up.railway.app',
    'localhost',
    '127.0.0.1',
])

# Remove duplicates and empty strings
ALLOWED_HOSTS = list(set([h for h in ALLOWED_HOSTS if h]))

# CRITICAL: CSRF settings for Railway
CSRF_TRUSTED_ORIGINS = []

# Add HTTPS versions of all allowed hosts
for host in ALLOWED_HOSTS:
    if host not in ['localhost', '127.0.0.1']:
        CSRF_TRUSTED_ORIGINS.append(f'https://{host}')
    CSRF_TRUSTED_ORIGINS.append(f'https://*.{host}')

# Add common patterns
CSRF_TRUSTED_ORIGINS.extend([
    'https://*.railway.app',
    'https://*.up.railway.app',
])

# Remove duplicates
CSRF_TRUSTED_ORIGINS = list(set(CSRF_TRUSTED_ORIGINS))

# CRITICAL: Trust Railway's proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Security settings - DISABLE TEMPORARILY for testing
SECURE_SSL_REDIRECT = False  # Set to True after testing
SESSION_COOKIE_SECURE = False  # Set to True after testing
CSRF_COOKIE_SECURE = False  # Set to True after testing
SECURE_HSTS_SECONDS = 0  # Set to 31536000 after testing

# Database - Railway provides DATABASE_URL
if 'DATABASE_URL' in os.environ:
    import dj_database_url
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        ssl_require=True
    )

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Add debug logging to see values
print("="*60)
print("PRODUCTION SETTINGS LOADED")
print(f"DEBUG: {DEBUG}")
print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"CSRF_TRUSTED_ORIGINS: {CSRF_TRUSTED_ORIGINS}")
print("="*60)