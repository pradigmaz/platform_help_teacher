"""
Аудит для бот-взаимодействий (Telegram/VK).
"""

import logging
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

from .constants import ActionType, EntityType
from .schemas import AuditContext
from .service import get_audit_service

logger = logging.getLogger(__name__)

Platform = Literal["telegram", "vk"]


async def _resolve_user_id(db: AsyncSession, social_id: int, platform: Platform) -> UUID | None:
    """Резолвит user_id по social_id."""
    field = User.telegram_id if platform == "telegram" else User.vk_id
    result = await db.execute(select(User.id).where(field == social_id))
    row = result.scalar_one_or_none()
    return row


async def log_bot_action(
    db: AsyncSession,
    action_type: ActionType,
    social_id: int,
    platform: Platform,
    username: str | None = None,
    extra_data: dict | None = None,
    user_id: UUID | None = None,
) -> None:
    """
    Логирует действие бота в аудит.

    Args:
        db: Сессия БД
        action_type: Тип действия (BOT_START, BOT_AUTH, etc.)
        social_id: ID пользователя в соцсети
        platform: Платформа (telegram/vk)
        username: Username в соцсети
        extra_data: Дополнительные данные (args, text, etc.)
        user_id: UUID пользователя (если известен)
    """
    # Резолвим user_id если не передан
    if user_id is None:
        user_id = await _resolve_user_id(db, social_id, platform)

    context = AuditContext(
        request_id=str(uuid4()),
        user_id=user_id,
        method="BOT",
        path=f"/bot/{platform}",
        ip_address="bot",  # Bot requests don't have IP
        action_type=action_type.value,
        entity_type=EntityType.BOT.value,
        extra_data={
            "social_id": social_id,
            "platform": platform,
            "username": username,
            **(extra_data or {}),
        },
    )

    audit_service = get_audit_service()
    await audit_service.write_log(context)


async def log_bot_start(
    db: AsyncSession,
    social_id: int,
    platform: Platform,
    username: str | None = None,
    args: str | None = None,
) -> None:
    """Логирует /start команду."""
    await log_bot_action(
        db=db,
        action_type=ActionType.BOT_START,
        social_id=social_id,
        platform=platform,
        username=username,
        extra_data={"has_deeplink": True} if args else None,
    )


async def log_bot_auth(
    db: AsyncSession,
    social_id: int,
    platform: Platform,
    user_id: UUID,
    username: str | None = None,
) -> None:
    """Логирует генерацию OTP для входа."""
    await log_bot_action(
        db=db,
        action_type=ActionType.BOT_AUTH,
        social_id=social_id,
        platform=platform,
        username=username,
        user_id=user_id,
    )


async def log_bot_bind(
    db: AsyncSession,
    social_id: int,
    platform: Platform,
    user_id: UUID,
    username: str | None = None,
    bind_type: str = "new",  # "new", "relink", "invite"
) -> None:
    """Логирует привязку аккаунта."""
    action = ActionType.BOT_RELINK if bind_type == "relink" else ActionType.BOT_BIND
    await log_bot_action(
        db=db,
        action_type=action,
        social_id=social_id,
        platform=platform,
        username=username,
        user_id=user_id,
        extra_data={"bind_type": bind_type},
    )


async def log_bot_message(
    db: AsyncSession,
    social_id: int,
    platform: Platform,
    text: str,
    username: str | None = None,
    context_type: str | None = None,  # "fio_input", "relink", etc.
) -> None:
    """Логирует текстовое сообщение."""
    await log_bot_action(
        db=db,
        action_type=ActionType.BOT_MESSAGE,
        social_id=social_id,
        platform=platform,
        username=username,
        extra_data={
            "context": context_type,
            "text_length": len(text),
        },
    )
