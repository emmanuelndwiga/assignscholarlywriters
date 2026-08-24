"""
Custom security middleware: CSP headers, clickjacking, referrer policy,
permissions policy, admin brute-force protection, and additional hardening.
"""
import time
import logging
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseForbidden

logger = logging.getLogger('django.security')


class SecurityHeadersMiddleware:
    """Add Content-Security-Policy and additional security headers."""

    _CSP_DIRECTIVES = [
        "default-src 'self'",
        "script-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://api.web3forms.com",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: https:",
        "connect-src 'self' https://api.web3forms.com",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self' https://api.web3forms.com",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not getattr(settings, 'DEBUG', False):
            response['Content-Security-Policy'] = '; '.join(self._CSP_DIRECTIVES)

        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = (
            'accelerometer=(), camera=(), geolocation=(), '
            'gyroscope=(), magnetometer=(), microphone=(), '
            'payment=(), usb=()'
        )

        return response


def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


class AdminLoginThrottleMiddleware:
    """
    Throttle POST /admin/login/ by IP using Django's cache framework.
    After MAX_ATTEMPTS failed attempts within LOCKOUT_SECONDS, return 429.
    Detects failed login: Django admin returns 200 (re-renders login form)
    on failure, 302 (redirect) on success.
    """

    _CACHE_PREFIX = 'admin_login_attempts_'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method != 'POST' or request.path != '/admin/login/':
            return self.get_response(request)

        max_attempts = getattr(settings, 'ADMIN_LOGIN_ATTEMPTS_ALLOWED', 5)
        lockout_seconds = getattr(settings, 'ADMIN_LOGIN_LOCKOUT_SECONDS', 900)

        ip = _get_client_ip(request)
        cache_key = self._CACHE_PREFIX + ip.replace('.', '_').replace(':', '_')

        attempts = cache.get(cache_key, [])

        # Prune old entries outside the lockout window
        now = time.time()
        attempts = [t for t in attempts if now - t < lockout_seconds]

        if len(attempts) >= max_attempts:
            logger.warning(
                'Admin login throttle: IP %s blocked (%d attempts in %ds)',
                ip, len(attempts), lockout_seconds,
            )
            return HttpResponseForbidden(
                'Too many failed login attempts. Please try again later.'
            )

        response = self.get_response(request)

        # Django admin redirects (302) on successful login; 200 = still on login form = failure
        if response.status_code != 302:
            attempts.append(now)
            cache.set(cache_key, attempts, lockout_seconds)
            logger.info(
                'Admin login failed from IP %s (%d/%d attempts)',
                ip, len(attempts), max_attempts,
            )
        else:
            cache.delete(cache_key)
            logger.info('Admin login successful from IP %s', ip)

        return response
