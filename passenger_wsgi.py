"""
Passenger WSGI file for cPanel deployment
"""
import os
import sys

# Add your project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'newsletter.settings.production'

# Import Django WSGI handler
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()