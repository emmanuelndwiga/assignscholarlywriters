"""
WSGI config for scholarlywriters_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os

# Fix SSL certificate verification on Windows / Python 3.14+
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
except ImportError:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scholarlywriters_backend.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
