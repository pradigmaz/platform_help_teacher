from fastapi_csrf_protect import CsrfProtect
from pydantic_settings import BaseSettings
from fastapi import Response
from app.core.config import settings


class CsrfSettings(BaseSettings):
    secret_key: str = settings.SECRET_KEY
    cookie_samesite: str = "lax"
    cookie_secure: bool = settings.ENVIRONMENT == "production"
    cookie_httponly: bool = False  # JS должен читать cookie для CSRF
    cookie_path: str = "/"  # Cookie доступен для всех путей
    token_location: str = "header"
    header_name: str = "X-CSRF-Token"
    header_type: str = ""
    cookie_key: str = "fastapi-csrf-token"


# Домен для cookie (None = текущий домен)
CSRF_COOKIE_DOMAIN: str | None = settings.COOKIE_DOMAIN


@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()


# Monkey-patch для поддержки cookie_domain
_original_set_csrf_cookie = CsrfProtect.set_csrf_cookie


def _patched_set_csrf_cookie(self, signed_token: str, response: Response) -> None:
    """Устанавливает CSRF cookie с поддержкой domain."""
    response.set_cookie(
        key=self._cookie_key,
        value=signed_token,
        secure=self._cookie_secure,
        httponly=self._cookie_httponly,
        samesite=self._cookie_samesite,
        path=self._cookie_path,
        domain=CSRF_COOKIE_DOMAIN,
    )


CsrfProtect.set_csrf_cookie = _patched_set_csrf_cookie
