"""Security header middleware."""
from django.conf import settings


class SecurityHeadersMiddleware:
    """Set security headers for API responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Roll out CSP in report-only mode first to avoid regressions.
        response['Content-Security-Policy-Report-Only'] = (
            settings.SECURITY_CSP_REPORT_ONLY
        )
        response.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
        response.setdefault('Cross-Origin-Resource-Policy', 'same-site')
        return response
