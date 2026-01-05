from fastapi_csrf_protect import CsrfProtect
from pydantic_settings import BaseSettings
from app.core.config import settings


class CsrfSettings(BaseSettings):
    secret_key: str = settings.SECRET_KEY
    cookie_samesite: str = "lax"
    cookie_secure: bool = settings.ENVIRONMENT == "production"
    cookie_httponly: bool = True
    token_location: str = "header"
    header_name: str = "X-CSRF-Token"
    header_type: str = ""


@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()
