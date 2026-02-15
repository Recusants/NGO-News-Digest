#!/usr/bin/python3
import os
import sys


# Write debug info
with open('/home/ngodiges/debug.log', 'w') as f:
    f.write(f"Python executable: {sys.executable}\n")
    f.write(f"Python path: {sys.path}\n")
    
    # Test PyMySQL import
    try:
        import pymysql
        f.write("pymysql imported SUCCESSFULLY\n")
        f.write(f"pymysql location: {pymysql.__file__}\n")
    except ImportError as e:
        f.write(f"pymysql import FAILED: {e}\n")



# Your cPanel ngodiges
username = 'ngodiges'

# Exact path to your app
project_path = f'/home/ngodiges/public_html/NGO-News-Digest'

# Add to Python path
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsletter.settings.production')

# Try to import Django and create application
try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
except Exception as e:
    # Log error to file for debugging
    with open('/home/ngodiges/passenger_error.log', 'w') as f:
        f.write(str(e))
    raise e