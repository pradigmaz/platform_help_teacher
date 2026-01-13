"""Генерация OTP и relink-кодов."""
import json
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, Group
from app.core.redis import get_redis
from app.utils.codes import generate_otp as gen_otp, generate_relink_code as gen_relink, mask_code
from .constants import Platform, RELINK_TTL, OTP_TTL

logger = logging.getLogger(__name__)


async def generate_relink_code(db: AsyncSession, user_id: UUID, platform: Platform) -> str:
    """
    Генерирует код для привязки/перепривязки аккаунта.
    Проверяет уникальность среди invite_code пользователей и групп.
    """
    redis = await get_redis()
    
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
        
        data = json.dumps({"user_id": str(user_id), "platform": platform})
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
