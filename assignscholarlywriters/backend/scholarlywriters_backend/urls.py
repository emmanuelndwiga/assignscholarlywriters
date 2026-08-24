import os
from pathlib import Path

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import Http404, FileResponse

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent


def serve_frontend(request, path=''):
    """Serve frontend files from the project root directory.
    Blocks access to backend/, .git/, __pycache__/, and other sensitive dirs.
    """
    blocked = {'backend', '.git', '.github', '__pycache__', 'node_modules', 'logs', 'staticfiles'}
    if path:
        first_part = path.split('/')[0]
        if first_part in blocked:
            raise Http404
    file_path = (FRONTEND_DIR / path).resolve()
    if not str(file_path).startswith(str(FRONTEND_DIR.resolve())):
        raise Http404
    if file_path.is_dir():
        index = file_path / 'index.html'
        if index.exists():
            return FileResponse(open(index, 'rb'), content_type='text/html')
        raise Http404
    if file_path.exists() and file_path.is_file():
        content_type = {
            '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
            '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png',
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif',
            '.ico': 'image/x-icon', '.woff': 'font/woff', '.woff2': 'font/woff2',
            '.ttf': 'font/ttf', '.txt': 'text/plain', '.xml': 'application/xml',
            '.pdf': 'application/pdf', '.webp': 'image/webp',
        }.get(file_path.suffix.lower(), 'application/octet-stream')
        return FileResponse(open(file_path, 'rb'), content_type=content_type)
    raise Http404


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/services/', include('services.urls')),
    path('api/pricing/', include('pricing.urls')),
    path('api/currencies/', include('currencies.urls')),
    path('api/quotations/', include('quotations.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/customers/', include('customers.urls')),
    path('api/samples/', include('samples.urls')),
    path('api/contact/', include('contact.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Frontend catch-all: serves HTML, CSS, JS, images at natural URLs.
# Must be LAST so API/admin routes take priority.
urlpatterns += [
    re_path(r'^(?P<path>.*)$', serve_frontend, name='frontend'),
]
