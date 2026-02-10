"""
Telegram-specific сервис.
Делегирует основную логику в bot_service.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import bot_service

# Re-export для обратной совместимости
RELINK_TTL = bot_service.RELINK_TTL


async def generate_relink_code(db: AsyncSession, user_id: UUID) -> str:
    """Генерирует код для перепривязки Telegram."""
    return await bot_service.generate_relink_code(db, user_id, "telegram")


async def generate_otp(telegram_id: int) -> str:
    """Генерирует OTP код для входа через Telegram."""
    return await bot_service.generate_otp(telegram_id, "telegram")


async def process_start_command(db: AsyncSession, social_id: int, username: str | None) -> str:
    """Обработка команды /start для Telegram (только приветствие/OTP)."""
    return await bot_service.process_start_command(db=db, social_id=social_id, username=username, platform="telegram")


async def process_code_command(
    db: AsyncSession, social_id: int, full_name: str, username: str | None, code: str
) -> str:
    """Обработка команды /code для Telegram (ввод кодов)."""
    return await bot_service.process_code_command(
        db=db, social_id=social_id, full_name=full_name, username=username, code=code, platform="telegram"
    )


async def process_text_message(db: AsyncSession, social_id: int, text: str, username: str | None) -> str | None:
    """Обработка текстовых сообщений для Telegram."""
    return await bot_service.process_text_message(
        db=db, social_id=social_id, text=text, username=username, platform="telegram"
    )


async def process_schedule_command(db: AsyncSession, social_id: int) -> str | None:
    """Обработка команды /schedule для Telegram (расписание преподавателя)."""
    return await bot_service.process_schedule_command(db=db, social_id=social_id, platform="telegram")
