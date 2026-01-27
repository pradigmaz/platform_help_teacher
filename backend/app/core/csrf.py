from fastapi_csrf_protect import CsrfProtect
from pydantic_settings import BaseSettings
from fastapi import Response
from app.core.config import settings


# Конфиг CSRF
CSRF_COOKIE_KEY = "fastapi-csrf-token"
CSRF_COOKIE_SAMESITE = "lax"
CSRF_COOKIE_SECURE = settings.ENVIRONMENT == "production"
CSRF_COOKIE_HTTPONLY = False  # JS должен читать cookie
CSRF_COOKIE_PATH = "/"
CSRF_COOKIE_DOMAIN: str | None = settings.COOKIE_DOMAIN


class CsrfSettings(BaseSettings):
    secret_key: str = settings.SECRET_KEY
    cookie_samesite: str = CSRF_COOKIE_SAMESITE
    cookie_secure: bool = CSRF_COOKIE_SECURE
    cookie_httponly: bool = CSRF_COOKIE_HTTPONLY
    cookie_path: str = CSRF_COOKIE_PATH
    token_location: str = "header"
    header_name: str = "X-CSRF-Token"
    header_type: str = ""
    cookie_key: str = CSRF_COOKIE_KEY


@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()


# Monkey-patch для поддержки cookie_domain (библиотека не поддерживает нативно)
_original_set_csrf_cookie = CsrfProtect.set_csrf_cookie


def _patched_set_csrf_cookie(self, signed_token: str, response: Response) -> None:
    """Устанавливает CSRF cookie с поддержкой domain."""
    response.set_cookie(
        key=CSRF_COOKIE_KEY,
        value=signed_token,
        secure=CSRF_COOKIE_SECURE,
        httponly=CSRF_COOKIE_HTTPONLY,
        samesite=CSRF_COOKIE_SAMESITE,
        path=CSRF_COOKIE_PATH,
        domain=CSRF_COOKIE_DOMAIN,
    )


CsrfProtect.set_csrf_cookie = _patched_set_csrf_cookie
