"""
Redis helpers for rate-limit admin unban flows.
"""

from uuid import UUID

from app.core.redis import get_redis

from .constants import REDIS_429_COUNT, REDIS_BAN
from .models import RateLimitWarning


def _ban_key(identifier: str) -> str:
    return REDIS_BAN.format(identifier=identifier)


def _count_key(identifier: str) -> str:
    return REDIS_429_COUNT.format(identifier=identifier)


async def clear_warning_unban_side_effects(warning: RateLimitWarning) -> None:
    redis = await get_redis()
    if redis is None:
        return

    identifiers = [f"ip:{warning.ip_address}"]
    if warning.user_id is not None:
        identifiers.append(f"user:{warning.user_id}")

    for identifier in identifiers:
        await redis.delete(_ban_key(identifier))
        await redis.delete(_count_key(identifier))


async def clear_user_unban_side_effects(user_id: UUID) -> None:
    redis = await get_redis()
    if redis is None:
        return

    identifier = f"user:{user_id}"
    await redis.delete(_ban_key(identifier))
    await redis.delete(_count_key(identifier))
