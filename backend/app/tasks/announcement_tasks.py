"""Celery tasks for one-time announcement delivery."""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import requests  # type: ignore[import-untyped]
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.time_constants import TELEGRAM_SEND_TIMEOUT_SECONDS
from app.db.session import SyncSessionLocal
from app.models.announcement import Announcement, AnnouncementSendStatus
from app.models.notification_settings import NotificationSettings
from app.models.user import User, UserRole
from app.services.announcement_service import build_delivery_stats, format_announcement_message

logger = logging.getLogger(__name__)


def _get_announcement(db: Session, announcement_id: UUID) -> Announcement | None:
    result = db.execute(select(Announcement).where(Announcement.id == announcement_id))
    return result.scalar_one_or_none()


def _get_students_for_notification(db: Session) -> list[tuple[User, NotificationSettings | None]]:
    result = db.execute(
        select(User, NotificationSettings)
        .outerjoin(NotificationSettings, User.id == NotificationSettings.user_id)
        .where(User.role == UserRole.STUDENT)
    )
    return [(user, notification_settings) for user, notification_settings in result.all()]


def _send_telegram_sync(chat_id: int, message: str) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN:
        return False

    response = requests.post(
        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": message},
        timeout=TELEGRAM_SEND_TIMEOUT_SECONDS,
    )
    return bool(response.status_code == 200)


def _send_vk_sync(user_id: int, message: str) -> bool:
    from app.bots.vk_bot import send_message_sync

    return send_message_sync(user_id, message)


def _finalize_success(db: Session, announcement: Announcement, stats: dict[str, int]) -> None:
    announcement.send_status = AnnouncementSendStatus.SENT
    announcement.sent_at = datetime.now(UTC)
    announcement.delivery_stats = stats
    announcement.delivery_error = None
    db.commit()


def _finalize_failure(
    db: Session, announcement: Announcement | None, error: str, stats: dict[str, int] | None = None
) -> None:
    if announcement is None:
        return

    announcement.send_status = AnnouncementSendStatus.FAILED
    announcement.delivery_error = error[:1000]
    if stats is not None:
        announcement.delivery_stats = stats
    db.commit()


@celery_app.task(
    name="app.tasks.announcement_tasks.send_announcement_task",
    acks_late=True,
)
def send_announcement_task(announcement_id: str) -> dict[str, Any]:
    stats = build_delivery_stats()

    try:
        with SyncSessionLocal() as db:
            announcement = _get_announcement(db, UUID(announcement_id))
            if announcement is None:
                logger.warning("announcement_send_skipped reason=missing announcement_id=%s", announcement_id)
                return {"status": "missing"}

            if announcement.is_draft:
                _finalize_failure(db, announcement, "Draft announcement cannot be delivered", stats)
                return {"status": AnnouncementSendStatus.FAILED.value, "stats": stats}

            if announcement.send_status is not AnnouncementSendStatus.SENDING:
                logger.warning(
                    "announcement_send_skipped reason=unexpected_status announcement_id=%s status=%s",
                    announcement_id,
                    announcement.send_status.value,
                )
                return {"status": announcement.send_status.value}

            message = format_announcement_message(announcement)
            students = _get_students_for_notification(db)

            for user, notification_settings in students:
                if notification_settings is None or not notification_settings.notify_announcements:
                    stats["skipped"] += 1
                    continue

                attempted_delivery = False

                if notification_settings.channel_telegram and user.telegram_id:
                    attempted_delivery = True
                    try:
                        if _send_telegram_sync(user.telegram_id, message):
                            stats["telegram_sent"] += 1
                        else:
                            stats["errors"] += 1
                    except Exception as exc:
                        logger.error("announcement_telegram_send_failed user_id=%s error=%s", user.id, exc)
                        stats["errors"] += 1

                if notification_settings.channel_vk and user.vk_id:
                    attempted_delivery = True
                    try:
                        if _send_vk_sync(user.vk_id, message):
                            stats["vk_sent"] += 1
                        else:
                            stats["errors"] += 1
                    except Exception as exc:
                        logger.error("announcement_vk_send_failed user_id=%s error=%s", user.id, exc)
                        stats["errors"] += 1

                if not attempted_delivery:
                    stats["skipped"] += 1

            _finalize_success(db, announcement, stats)
            logger.info("announcement_send_completed announcement_id=%s stats=%s", announcement_id, stats)
            return {"status": AnnouncementSendStatus.SENT.value, "stats": stats}
    except Exception as exc:
        logger.exception("announcement_send_failed announcement_id=%s", announcement_id)
        with SyncSessionLocal() as db:
            announcement = _get_announcement(db, UUID(announcement_id))
            _finalize_failure(db, announcement, str(exc), stats)
        raise
