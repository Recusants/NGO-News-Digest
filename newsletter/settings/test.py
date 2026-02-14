"""
Test settings - for CI/CD and testing
"""
from .base import *

# Use in-memory SQLite for fast tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Faster password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use console email backend (don't actually send emails)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable debug for tests (closer to production behavior)
DEBUG = False

# Simple secret key for tests
SECRET_KEY = 'django-insecure-test-key-for-ci'

# Allow all hosts during testing
ALLOWED_HOSTS = ['*']

# Disable security middleware that might interfere with tests
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Optional: Disable migrations for faster tests (if your models are stable)
# class DisableMigrations:
#     def __contains__(self, item):
#         return True
#
#     def __getitem__(self, item):
#         return None
#
# MIGRATION_MODULES = DisableMigrations()