"""Генерация OTP и relink-кодов."""
import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models import Group, User
from app.utils.codes import generate_otp as gen_otp
from app.utils.codes import generate_relink_code as gen_relink
from app.utils.codes import mask_code

from .constants import OTP_TTL, RELINK_TTL, Platform

logger = logging.getLogger(__name__)


async def generate_relink_code(
    db: AsyncSession,
    user_id: UUID,
    platform: Platform,
    current_social_id: int | None = None
) -> str:
    """
    Генерирует код для привязки/перепривязки аккаунта.
    Проверяет уникальность среди invite_code пользователей и групп.

    SECURITY: Сохраняет current_social_id для проверки при использовании кода.
    Если у пользователя уже есть привязка, код может использовать только он сам.
    """
    redis = await get_redis()

    # Получаем текущий social_id пользователя если не передан
    if current_social_id is None:
        from .users import get_social_id_field
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            field = get_social_id_field(platform)
            current_social_id = getattr(user, field.key)

    for _ in range(10):
        code = gen_relink()

        # Проверяем коллизии с существующими relink-кодами в Redis
        existing_relink = await redis.exists(f"relink:{code}")
        if existing_relink:
            continue

        # Проверяем коллизии с invite_code пользователей
        user_result = await db.execute(select(User.id).where(User.invite_code == code))
        if user_result.scalar_one_or_none():
            continue

        # Проверяем коллизии с invite_code групп
        group_result = await db.execute(select(Group.id).where(Group.invite_code == code))
        if group_result.scalar_one_or_none():
            continue

        # SECURITY: Сохраняем original_social_id для валидации при использовании
        data = json.dumps({
            "user_id": str(user_id),
            "platform": platform,
            "original_social_id": current_social_id  # None если первая привязка
        })
        await redis.setex(f"relink:{code}", RELINK_TTL, data)
        logger.info(f"Generated relink code {mask_code(code)} for user {user_id}, platform {platform}")
        return code

    raise RuntimeError("Failed to generate unique relink code")


async def generate_otp(social_id: int, platform: Platform) -> str:
    """Генерирует OTP код для входа."""
    otp = gen_otp()
    redis = await get_redis()
    data = json.dumps({"social_id": social_id, "platform": platform})
    await redis.setex(f"auth:{otp}", OTP_TTL, data)
    return otp
