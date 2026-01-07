"""
Telegram-specific сервис.
Делегирует основную логику в bot_service.
"""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.services import bot_service

# Re-export для обратной совместимости
RELINK_TTL = bot_service.RELINK_TTL


async def generate_relink_code(user_id: UUID) -> str:
    """Генерирует код для перепривязки Telegram."""
    return await bot_service.generate_relink_code(user_id, "telegram")


async def generate_otp(telegram_id: int) -> str:
    """Генерирует OTP код для входа через Telegram."""
    return await bot_service.generate_otp(telegram_id, "telegram")


async def process_start_command(
    db: AsyncSession,
    social_id: int,
    full_name: str,
    username: str | None,
    args: str | None
) -> str:
    """Обработка команды /start для Telegram."""
    return await bot_service.process_start_command(
        db=db,
        social_id=social_id,
        full_name=full_name,
        username=username,
        args=args,
        platform="telegram"
    )


async def process_text_message(
    db: AsyncSession,
    social_id: int,
    text: str,
    username: str | None
) -> str | None:
    """Обработка текстовых сообщений для Telegram."""
    return await bot_service.process_text_message(
        db=db,
        social_id=social_id,
        text=text,
        username=username,
        platform="telegram"
    )
