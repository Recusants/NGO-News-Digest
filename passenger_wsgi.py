import sys
import os

# Add project path
project_path = '/home/ngodiges/public_html/NGO-News-Digest'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Set environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsletter.settings.production')

# Import the Django WSGI application
from newsletter.wsgi import application
