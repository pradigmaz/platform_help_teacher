"""
Сервис для управления PIN-кодами и rate limiting попыток.
"""

import logging

from app.core.config import settings
from app.core.redis import get_redis
from app.core.time_constants import (
    CODE_ATTEMPTS_WINDOW_SECONDS,
)
from app.core.time_constants import (
    PIN_LOCKOUT_SECONDS as PIN_LOCKOUT_TIME,
)

logger = logging.getLogger(__name__)

PIN_LOCKOUT_SECONDS = PIN_LOCKOUT_TIME


class PinService:
    """Сервис для управления попытками ввода PIN."""

    def __init__(self, prefix: str = "report_pin"):
        self.prefix = prefix

    def _attempts_key(self, code: str, ip: str) -> str:
        return f"{self.prefix}_attempts:{code}:{ip}"

    def _lockout_key(self, code: str, ip: str) -> str:
        return f"{self.prefix}_lockout:{code}:{ip}"

    async def check_lockout(self, code: str, ip: str) -> int | None:
        """
        Проверка блокировки.
        Возвращает оставшееся время блокировки в секундах или None.
        """
        try:
            redis = await get_redis()
            if not redis:
                return None

            ttl = await redis.ttl(self._lockout_key(code, ip))
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.warning(f"Redis error in check_lockout: {e}")
            return None

    async def increment_attempts(self, code: str, ip: str) -> int:
        """
        Увеличить счётчик попыток.
        Возвращает количество оставшихся попыток.
        """
        try:
            redis = await get_redis()
            if not redis:
                return settings.MAX_PIN_ATTEMPTS - 1

            attempts_key = self._attempts_key(code, ip)
            attempts = await redis.incr(attempts_key)
            await redis.expire(attempts_key, CODE_ATTEMPTS_WINDOW_SECONDS)

            if attempts >= settings.MAX_PIN_ATTEMPTS:
                await redis.setex(self._lockout_key(code, ip), PIN_LOCKOUT_SECONDS, "1")
                await redis.delete(attempts_key)
                return 0

            return settings.MAX_PIN_ATTEMPTS - attempts
        except Exception as e:
            logger.warning(f"Redis error in increment_attempts: {e}")
            return settings.MAX_PIN_ATTEMPTS - 1

    async def reset_attempts(self, code: str, ip: str) -> None:
        """Сбросить счётчик после успешного ввода."""
        try:
            redis = await get_redis()
            if redis:
                await redis.delete(self._attempts_key(code, ip))
        except Exception as e:
            logger.warning(f"Redis error in reset_attempts: {e}")


# Singleton для отчётов
report_pin_service = PinService(prefix="report_pin")
