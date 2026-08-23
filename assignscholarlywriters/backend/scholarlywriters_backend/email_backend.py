"""
Custom SMTP email backend that handles SSL certificate issues
on Windows with Python 3.14+ (stricter OpenSSL rejects some CA bundles).
"""
import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend


class SSLFriendlyEmailBackend(EmailBackend):
    """
    SMTP backend that creates an SSL context with fallback.
    First tries normal verification; if it fails on this platform,
    falls back to unverified TLS (safe for dev / known SMTP servers).
    """

    def _make_ssl_context(self):
        # Try strict verification first
        ctx = ssl.create_default_context()
        # Test if it actually works against the target server
        try:
            test = smtplib.SMTP(self.host, self.port, timeout=5)
            test.starttls(context=ctx)
            test.quit()
            return ctx
        except ssl.SSLError:
            pass
        except Exception:
            return ctx  # Non-SSL error, return strict context anyway

        # Fallback: unverified TLS (no cert validation)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
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
