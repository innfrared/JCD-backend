"""Helpers for setting and clearing auth cookies."""
from django.conf import settings
from rest_framework_simplejwt.settings import api_settings


def _base_cookie_kwargs() -> dict:
    return {
        "secure": settings.AUTH_COOKIE_SECURE,
        "httponly": True,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
        "domain": settings.AUTH_COOKIE_DOMAIN,
    }


def set_access_cookie(response, access_token: str) -> None:
    max_age = int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds())
    response.set_cookie(
        settings.AUTH_ACCESS_COOKIE_NAME,
        access_token,
        max_age=max_age,
        path=settings.AUTH_ACCESS_COOKIE_PATH,
        **_base_cookie_kwargs(),
    )


def set_refresh_cookie(response, refresh_token: str) -> None:
    max_age = int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds())
    response.set_cookie(
        settings.AUTH_REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=max_age,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        **_base_cookie_kwargs(),
    )


def clear_auth_cookies(response) -> None:
    response.delete_cookie(
        settings.AUTH_ACCESS_COOKIE_NAME,
        path=settings.AUTH_ACCESS_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
    )
    response.delete_cookie(
        settings.AUTH_REFRESH_COOKIE_NAME,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
    )
