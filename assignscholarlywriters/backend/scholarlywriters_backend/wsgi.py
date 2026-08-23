"""
WSGI config for scholarlywriters_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""
import os
from pathlib import Path

# Fix SSL certificate verification on Windows / Python 3.14+
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
except ImportError:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scholarlywriters_backend.settings')

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

django_app = get_wsgi_application()

_backend_dir = Path(__file__).resolve().parent.parent
_frontend_dir = _backend_dir.parent

application = WhiteNoise(django_app)

# Serve the frontend files at their natural URLs (CSS, JS, HTML, images, etc.)
# Exclude the backend/ directory so .env, manage.py, etc. are never served.
if _frontend_dir.exists():
    application.add_files(
        str(_frontend_dir),
        prefix='',
        ignore=['backend', '.git', '.github', 'node_modules', '__pycache__'],
    )

# Serve Django's collected static files at /static/
_static_root = _backend_dir / 'staticfiles'
if _static_root.exists():
    application.add_files(str(_static_root), prefix='static/')
