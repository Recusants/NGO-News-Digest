from .common import *

DEBUG = True

SECRET_KEY = 'django-insecure-aoti*^1&3g_+%-3_(5ve#yr+2(ytdh1r0%+o1@xqt%x3b@7gdo'

ALLOWED_HOSTS = ['*']


PROJECT_ROOT = os.path.dirname(BASE_DIR)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT , 'db.sqlite3'),   
    }
}




# ----------------------------------------------------------------------------------------------------





# Database


# Email settings for development
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tinashemphisa45@gmail.com'
EMAIL_HOST_PASSWORD = 'ztej qsoa dngh zcgu'
DEFAULT_FROM_EMAIL = 'tinashemphisa45@gmail.com'

SITE_URL = 'http://127.0.0.1:8000'

# # Optional: Add Django Debug Toolbar for development
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
# INTERNAL_IPS = ['127.0.0.1']





