"""
WSGI config for newsletter project.

"""

import os
from django.core.wsgi import get_wsgi_application

# Use production settings by default for deployment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsletter.settings.production')

application = get_wsgi_application()