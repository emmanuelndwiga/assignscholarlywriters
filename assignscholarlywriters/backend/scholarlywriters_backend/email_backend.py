"""
Custom SMTP email backend that handles SSL certificate issues
on Windows with Python 3.14+ (stricter OpenSSL rejects some CA bundles).
In production, always uses strict SSL verification.
"""
import ssl
import smtplib
from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend


class SSLFriendlyEmailBackend(EmailBackend):
    """
    SMTP backend that creates an SSL context with fallback.
    In production (DEBUG=False), always uses strict verification.
    In development, falls back to unverified TLS if strict fails.
    """

    def _make_ssl_context(self):
        # Always try strict verification first
        ctx = ssl.create_default_context()

        if getattr(settings, 'DEBUG', False):
            # Dev only: test if strict works, fall back if not
            try:
                test = smtplib.SMTP(self.host, self.port, timeout=5)
                test.starttls(context=ctx)
                test.quit()
                return ctx
            except ssl.SSLError:
                pass
            except Exception:
                return ctx

            # Dev fallback: unverified TLS
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx

        # Production: always strict verification
        return ctx

    def open(self):
        if self.connection:
            return False

        connection_params = {'host': self.host, 'port': self.port}
        if self.timeout is not None:
            connection_params['timeout'] = self.timeout

        self.connection = smtplib.SMTP(**connection_params)
        self.connection.ehlo()

        if self.use_tls:
            ssl_context = self._make_ssl_context()
            self.connection.starttls(context=ssl_context)
            self.connection.ehlo()

        if self.username and self.password:
            self.connection.login(self.username, self.password)

        return True
