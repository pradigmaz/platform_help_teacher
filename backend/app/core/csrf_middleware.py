"""
CSRF Middleware для защиты мутирующих запросов.
Применяется ко всем POST/PUT/DELETE/PATCH запросам.
"""

import logging
from collections.abc import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Endpoints исключённые из CSRF проверки
CSRF_EXEMPT_PATHS: set[str] = {
    "/api/v1/webhooks/telegram",  # Telegram webhook (проверяется по IP + secret)
    "/api/v1/webhooks/vk",  # VK webhook
    "/api/v1/auth/csrf-token",  # Получение CSRF токена
    "/api/v1/admin/schedule/parse",  # Парсинг расписания (защищён JWT)
    "/api/v1/admin/schedule/parse-now",  # Ручной парсинг (защищён JWT)
    "/api/v1/admin/schedule/parser-config",  # Конфиг парсера (защищён JWT)
    "/api/v1/admin/backups",  # Бэкапы (защищены JWT)
    "/health",  # Health check
    "/docs",  # Swagger
    "/openapi.json",  # OpenAPI spec
}

# Методы требующие CSRF защиты
PROTECTED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware для автоматической CSRF валидации.

    Проверяет X-CSRF-Token заголовок для всех мутирующих запросов,
    кроме исключённых путей (webhooks, health checks).
    """

    async def dispatch(self, request: Request, call_next: Callable):
        # Пропускаем безопасные методы
        if request.method not in PROTECTED_METHODS:
            return await call_next(request)

        # Пропускаем исключённые пути
        path = request.url.path
        if self._is_exempt(path):
            return await call_next(request)

        # Валидируем CSRF токен
        try:
            csrf_protect = CsrfProtect()
            await csrf_protect.validate_csrf(request)
        except CsrfProtectError as e:
            logger.warning(
                f"CSRF validation failed: {path} | "
                f"IP: {request.client.host if request.client else 'unknown'} | "
                f"Error: {e.message}"
            )
            return JSONResponse(status_code=e.status_code, content={"detail": e.message})
        except Exception as e:
            logger.error(f"CSRF middleware error: {e}")
            return JSONResponse(status_code=403, content={"detail": "CSRF validation error"})

        return await call_next(request)

    def _is_exempt(self, path: str) -> bool:
        """Проверяет, исключён ли путь из CSRF защиты."""
        # Точное совпадение
        if path in CSRF_EXEMPT_PATHS:
            return True

        # Префиксное совпадение для webhooks
        return bool(path.startswith("/api/v1/webhooks/"))


def add_csrf_exempt_path(path: str) -> None:
    """Добавить путь в исключения CSRF."""
    CSRF_EXEMPT_PATHS.add(path)
