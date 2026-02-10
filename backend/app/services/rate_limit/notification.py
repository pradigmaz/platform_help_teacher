"""
Уведомления преподавателям о rate limit нарушениях.
"""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.telegram_bot import bot
from app.models.user import User

from .constants import MESSAGES, WarningLevel
from .models import RateLimitWarning

logger = logging.getLogger(__name__)


async def notify_admins_about_violation(
    db: AsyncSession,
    warning: RateLimitWarning,
    user: User | None = None,
) -> bool:
    """
    Отправляет уведомление админам/преподавателям о нарушении.

    Returns:
        True если уведомление отправлено
    """
    try:
        # Получаем админов с telegram_id
        result = await db.execute(
            select(User).where(
                User.is_superuser,
                User.telegram_id.isnot(None),
            )
        )
        admins = result.scalars().all()

        if not admins:
            logger.warning("No admins with telegram_id found for rate limit notification")
            return False

        # Формируем сообщение
        user_info = "Неизвестный пользователь"
        if user:
            user_info = f"{user.full_name} (ID: {user.id})"
        elif warning.user_id:
            user_info = f"User ID: {warning.user_id}"

        level_emoji = {
            WarningLevel.SOFT_BAN.value: "⚠️",
            WarningLevel.HARD_BAN.value: "🚫",
        }.get(warning.warning_level, "ℹ️")

        message = (
            f"{level_emoji} Rate Limit Alert\n\n"
            f"👤 {user_info}\n"
            f"🌐 IP: {warning.ip_address}\n"
            f"📊 Нарушений: {warning.violation_count}\n"
            f"⏱ Уровень: {warning.warning_level}\n"
        )

        if warning.ban_until:
            message += f"🔒 Бан до: {warning.ban_until.strftime('%H:%M:%S')}\n"

        message += "\n💡 Разбан: /admin/rate-limits"

        # Отправляем всем админам
        sent = False
        for admin in admins:
            try:
                await bot.send_message(chat_id=admin.telegram_id, text=message)
                sent = True
                logger.info(f"Rate limit notification sent to admin {admin.id}")
            except Exception as e:
                logger.error(f"Failed to send notification to admin {admin.id}: {e}")

        return sent

    except Exception as e:
        logger.error(f"Error sending rate limit notification: {e}")
        return False


async def record_warning_to_db(
    db: AsyncSession,
    ip_address: str,
    level: WarningLevel,
    violation_count: int,
    user_id: UUID | None = None,
    fingerprint_hash: str | None = None,
    ban_duration: int = 0,
    notify: bool = False,
) -> RateLimitWarning | None:
    """
    Записывает предупреждение в БД и отправляет уведомление если нужно.
    """
    from datetime import datetime, timedelta

    try:
        ban_until = None
        if ban_duration > 0:
            ban_until = datetime.utcnow() + timedelta(seconds=ban_duration)

        warning = RateLimitWarning(
            user_id=user_id,
            ip_address=ip_address,
            fingerprint_hash=fingerprint_hash,
            warning_level=level.value,
            violation_count=violation_count,
            message=MESSAGES.get(level),
            ban_until=ban_until,
            admin_notified=False,
        )

        db.add(warning)
        await db.commit()
        await db.refresh(warning)

        # Отправляем уведомление если нужно
        if notify:
            user = None
            if user_id:
                user = await db.get(User, user_id)

            notified = await notify_admins_about_violation(db, warning, user)
            if notified:
                warning.admin_notified = True
                await db.commit()

        return warning

    except Exception as e:
        logger.error(f"Error recording rate limit warning: {e}")
        await db.rollback()
        return None
