import os
from django.core.wsgi import get_wsgi_application

# Set settings module based on environment
if os.environ.get('DJANGO_ENV') == 'production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsletter.settings.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsletter.settings.development')

application = get_wsgi_application()