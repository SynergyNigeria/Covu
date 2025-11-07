"""
Custom email backend for COVU Marketplace
Handles SSL certificate verification properly for Python 3.13+
Uses certifi for trusted CA certificates
"""

from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.conf import settings
import ssl
import certifi


class CustomEmailBackend(SMTPBackend):
    """
    Custom email backend that properly handles SSL certificates
    """

    def open(self):
        """
        Override open to use proper SSL context with certifi certificates
        """
        if self.connection:
            return False

        connection_params = {}
        if self.timeout is not None:
            connection_params["timeout"] = self.timeout

        # Create SSL context with certifi certificates
        if self.use_ssl or self.use_tls:
            # Production: Use proper SSL context with certifi
            if not settings.DEBUG:
                context = ssl.create_default_context(cafile=certifi.where())
            else:
                # Development: Allow unverified context (for testing)
                context = ssl._create_unverified_context()

            if self.use_ssl:
                connection_params["context"] = context

        try:
            self.connection = self.connection_class(
                self.host, self.port, **connection_params
            )

            # TLS/STARTTLS
            if self.use_tls:
                # Use proper context for TLS
                if not settings.DEBUG:
                    tls_context = ssl.create_default_context(cafile=certifi.where())
                else:
                    tls_context = ssl._create_unverified_context()

                self.connection.starttls(context=tls_context)

            # Authenticate
            if self.username and self.password:
                self.connection.login(self.username, self.password)

            return True

        except Exception as e:
            if not self.fail_silently:
                raise
            return False
