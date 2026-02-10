"""Rate limiting для бот-команд."""

import logging

from app.core.redis import get_redis

from .constants import (
    CODE_ATTEMPTS_WINDOW,
    CODE_LOCKOUT_SECONDS,
    MAX_CODE_ATTEMPTS,
    Platform,
)

logger = logging.getLogger(__name__)


async def check_code_rate_limit(social_id: int, platform: Platform) -> tuple[bool, int | None]:
    """
    Проверяет rate limit для ввода кодов.

    Returns:
        (allowed, lockout_remaining): allowed=True если можно продолжить,
        lockout_remaining — оставшееся время блокировки в секундах.
    """
    redis = await get_redis()
    lockout_key = f"bot_code_lockout:{platform}:{social_id}"

    lockout_ttl = await redis.ttl(lockout_key)
    if lockout_ttl > 0:
        return False, lockout_ttl

    return True, None


async def increment_code_attempts(social_id: int, platform: Platform) -> int:
    """
    Увеличивает счётчик попыток ввода кода.

    Returns:
        Количество оставшихся попыток (0 = заблокирован).
    """
    redis = await get_redis()
    attempts_key = f"bot_code_attempts:{platform}:{social_id}"
    lockout_key = f"bot_code_lockout:{platform}:{social_id}"

    attempts = await redis.incr(attempts_key)
    await redis.expire(attempts_key, CODE_ATTEMPTS_WINDOW)

    if attempts >= MAX_CODE_ATTEMPTS:
        await redis.setex(lockout_key, CODE_LOCKOUT_SECONDS, "1")
        await redis.delete(attempts_key)
        logger.warning(f"Bot code rate limit exceeded for {platform}:{social_id}")
        return 0

    return MAX_CODE_ATTEMPTS - attempts


async def reset_code_attempts(social_id: int, platform: Platform) -> None:
    """Сбрасывает счётчик попыток после успешного ввода."""
    redis = await get_redis()
    await redis.delete(f"bot_code_attempts:{platform}:{social_id}")
