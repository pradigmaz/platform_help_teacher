"""
Celery tasks for automated backups.
Reads settings from DB for dynamic scheduling.

ВАЖНО: Используем синхронные операции для совместимости с Celery prefork worker.
asyncio.run() / asyncio.new_event_loop() в prefork вызывает "Event loop is closed".
"""

import logging
import traceback

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.time_constants import BACKUP_DUMP_TIMEOUT_SECONDS, BACKUP_UPLOAD_TIMEOUT_SECONDS
from app.db.session import SyncSessionLocal
from app.services.schedule_constants import now_msk

logger = logging.getLogger(__name__)

# Retry delays for failed tasks (1min, 5min, 15min)
RETRY_DELAYS = [60, 300, 900]


def _get_backup_settings_sync() -> dict:
    """Fetch backup settings from database (sync version)."""
    from app.models.backup_settings import BackupSettings

    with SyncSessionLocal() as db:
        result = db.execute(select(BackupSettings).where(BackupSettings.id == 1))
        settings = result.scalar_one_or_none()

        if settings:
            return {
                "enabled": settings.enabled,
                "retention_days": settings.retention_days,
                "max_backups": settings.max_backups,
                "schedule_hour": settings.schedule_hour,
                "schedule_minute": settings.schedule_minute,
                "notify_on_success": settings.notify_on_success,
                "notify_on_failure": settings.notify_on_failure,
            }
        # Defaults
        return {
            "enabled": True,
            "retention_days": 30,
            "max_backups": 10,
            "schedule_hour": 17,
            "schedule_minute": 0,
            "notify_on_success": False,
            "notify_on_failure": True,
        }


def _is_backup_due(schedule_hour: int, schedule_minute: int) -> bool:
    """Check whether the scheduled backup should run in the current minute."""
    now = now_msk()
    return now.hour == schedule_hour and now.minute == schedule_minute


def _cleanup_with_limits_sync(service, retention_days: int, max_backups: int) -> int:
    """
    Cleanup backups by both retention period AND max count (sync version).
    Returns total deleted count.
    """
    deleted = 0

    # 1. Delete by retention period
    deleted += service.cleanup_old_backups_sync(retention_days)

    # 2. Delete excess backups beyond max_backups limit
    backups = service.list_backups_sync()
    if len(backups) > max_backups:
        excess = backups[max_backups:]
        for backup in excess:
            try:
                if service.delete_backup_sync(backup.key):
                    deleted += 1
                    logger.info(f"Deleted excess backup (max_backups limit): {backup.key}")
            except Exception as e:
                logger.error(f"Failed to delete excess backup {backup.key}: {e}")

    return deleted


@celery_app.task(
    name="app.tasks.backup_tasks.create_scheduled_backup",
    bind=True,
    max_retries=3,
    acks_late=True,
    soft_time_limit=BACKUP_DUMP_TIMEOUT_SECONDS + BACKUP_UPLOAD_TIMEOUT_SECONDS,
)
def create_scheduled_backup(self):
    """
    Create scheduled backup with dynamic settings from DB.
    Checks if backup is enabled and applies max_backups limit.
    Called by celery beat at scheduled time (crontab).

    Использует синхронные операции для совместимости с prefork worker.
    """
    logger.info("=== SCHEDULED BACKUP TASK STARTED ===")
    db_settings = {
        "notify_on_failure": True,
    }

    try:
        logger.info("Fetching backup settings from DB...")
        db_settings = _get_backup_settings_sync()
        logger.info(f"Backup settings: enabled={db_settings['enabled']}")

        if not db_settings["enabled"]:
            logger.info("Scheduled backup skipped: backups disabled in settings")
            return {"success": True, "reason": "disabled", "ran": False}

        if not _is_backup_due(db_settings["schedule_hour"], db_settings["schedule_minute"]):
            logger.debug(
                "Scheduled backup skipped: current time does not match %02d:%02d MSK",
                db_settings["schedule_hour"],
                db_settings["schedule_minute"],
            )
            return {"success": True, "reason": "not_due", "ran": False}

        logger.info("Starting scheduled backup...")

        from app.services.backup.backup_service import BackupService

        service = BackupService()
        result = service.create_backup_sync(
            send_to_admin=db_settings["notify_on_success"],
            notify_on_failure=db_settings["notify_on_failure"],
        )

        if result.success:
            logger.info(f"Scheduled backup completed: {result.backup_key}")
            if result.notification_error:
                logger.warning(result.notification_error)
            if result.offsite_error:
                logger.warning(result.offsite_error)
            deleted = _cleanup_with_limits_sync(service, db_settings["retention_days"], db_settings["max_backups"])
            if deleted:
                logger.info(f"Cleaned up {deleted} old backups")
        else:
            logger.error(f"Scheduled backup failed: {result.error}")
            raise RuntimeError(result.error or "Scheduled backup failed")

        return {
            "success": result.success,
            "key": result.backup_key,
            "ran": True,
            "notification_sent": result.notification_sent,
            "notification_error": result.notification_error,
        }

    except Exception as e:
        tb_text = traceback.format_exc()
        logger.error(f"Scheduled backup task failed: {e}\n{tb_text}")

        # Уведомляем админа только при финальном retry
        if db_settings.get("notify_on_failure", True) and self.request.retries >= self.max_retries:
            try:
                from app.services.backup.notification_sync import notify_backup_failure_sync

                notify_result = notify_backup_failure_sync(
                    f"Scheduled backup task failed after {self.max_retries} retries: {e}", traceback_text=tb_text
                )
                if not notify_result.success and notify_result.error:
                    logger.warning(notify_result.error)
            except Exception as notify_err:
                logger.error(f"Failed to send failure notification: {notify_err}")

        retry_delay = RETRY_DELAYS[min(self.request.retries, len(RETRY_DELAYS) - 1)]
        raise self.retry(exc=e, countdown=retry_delay)


@celery_app.task(
    name="app.tasks.backup_tasks.cleanup_old_backups", bind=True, max_retries=3, acks_late=True, soft_time_limit=120
)
def cleanup_old_backups(self, retention_days: int = None, max_backups: int = None):
    """
    Cleanup old backups beyond retention period and max count.
    Uses DB settings if parameters not provided.
    """
    logger.info("Starting backup cleanup...")

    try:
        if retention_days is None or max_backups is None:
            db_settings = _get_backup_settings_sync()
            retention_days = retention_days or db_settings["retention_days"]
            max_backups = max_backups or db_settings["max_backups"]

        from app.services.backup.backup_service import BackupService

        service = BackupService()
        deleted = _cleanup_with_limits_sync(service, retention_days, max_backups)

        logger.info(f"Cleanup completed: {deleted} backups deleted")
        return {"deleted": deleted}

    except Exception as e:
        logger.exception("Backup cleanup failed")
        retry_delay = RETRY_DELAYS[min(self.request.retries, len(RETRY_DELAYS) - 1)]
        raise self.retry(exc=e, countdown=retry_delay)
