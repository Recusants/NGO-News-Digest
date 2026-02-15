import os
import sys

# Write debug info to file
with open('/home/ngodiges/debug_import.log', 'w') as f:
    f.write("=== PASSENGER_WSGI START ===\n")
    f.write(f"Current directory: {os.getcwd()}\n")
    f.write(f"Python executable: {sys.executable}\n")
    f.write(f"Python version: {sys.version}\n")
        # f.write(f"Python path: {sys.path}\n\n")
        
        # # Check what's in site-packages
        # site_packages = [p for p in sys.path if 'site-packages' in p]
        # f.write(f"Site packages: {site_packages}\n\n")
    
    # Try to find where pymysql might be imported
    f.write("Attempting to trace imports...\n")

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsletter.settings.production')

try:
    # Try importing Django
    from django.core.wsgi import get_wsgi_application
    
    # Add more debug info after Django loads
    with open('/home/ngodiges/debug_import.log', 'a') as f:
        f.write("Django imported successfully\n")
        
        # Check settings module
        from django.conf import settings
        f.write(f"Settings module: {settings.SETTINGS_MODULE}\n")
        f.write(f"Database engine: {settings.DATABASES['default']['ENGINE']}\n")
    
    application = get_wsgi_application()
    
except Exception as e:
    with open('/home/ngodiges/debug_import.log', 'a') as f:
        f.write(f"ERROR: {e}\n")
        import traceback
        traceback.print_exc(file=f)
    raise e