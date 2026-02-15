import sys
import os
import traceback

# Add project directory to Python path
project_path = '/home/ngodiges/public_html/NGO-News-Digest'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Add parent directory as well
parent_path = '/home/ngodiges/public_html'
if parent_path not in sys.path:
    sys.path.insert(0, parent_path)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsletter.settings.production')

# Debug: Write to error log
with open('/home/ngodiges/passenger_debug.log', 'w') as f:
    f.write(f"Python executable: {sys.executable}\n")
    f.write(f"Python path: {sys.path}\n")
    f.write(f"Current directory: {os.getcwd()}\n")
    f.write(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}\n")

# Try to import Django and create application
try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    # Log success
    with open('/home/ngodiges/passenger_debug.log', 'a') as f:
        f.write("Django loaded successfully!\n")
except Exception as e:
    # Log the error to a file
    with open('/home/ngodiges/passenger_error.log', 'w') as f:
        f.write(f"Error loading Django: {e}\n")
        traceback.print_exc(file=f)
    
    # Return a simple error message
    def application(environ, start_response):
        status = '500 Internal Server Error'
        output = f"Error loading Django: {e}".encode()
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return [output]