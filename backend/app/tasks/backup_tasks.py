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
from app.db.session import SyncSessionLocal

logger = logging.getLogger(__name__)

# Retry delays for failed tasks (1min, 5min, 15min)
RETRY_DELAYS = [60, 300, 900]


def _get_backup_settings_sync() -> dict:
    """Fetch backup settings from database (sync version)."""
    from app.models.backup_settings import BackupSettings

    with SyncSessionLocal() as db:
        result = db.execute(
            select(BackupSettings).where(BackupSettings.id == 1)
        )
        settings = result.scalar_one_or_none()

        if settings:
            return {
                "enabled": settings.enabled,
                "retention_days": settings.retention_days,
                "max_backups": settings.max_backups,
                "schedule_hour": settings.schedule_hour,
                "schedule_minute": settings.schedule_minute,
            }
        # Defaults
        return {
            "enabled": True,
            "retention_days": 30,
            "max_backups": 10,
            "schedule_hour": 3,
            "schedule_minute": 0,
        }


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
                service.storage.delete_sync(backup.key)
                deleted += 1
                logger.info(f"Deleted excess backup (max_backups limit): {backup.key}")
            except Exception as e:
                logger.error(f"Failed to delete excess backup {backup.key}: {e}")

    return deleted


@celery_app.task(name="app.tasks.backup_tasks.create_scheduled_backup", bind=True, max_retries=3, acks_late=True, soft_time_limit=300)
def create_scheduled_backup(self):
    """
    Create scheduled backup with dynamic settings from DB.
    Checks if backup is enabled and applies max_backups limit.
    Called by celery beat at scheduled time (crontab).

    Использует синхронные операции для совместимости с prefork worker.
    """
    logger.info("=== SCHEDULED BACKUP TASK STARTED ===")

    try:
        logger.info("Fetching backup settings from DB...")
        db_settings = _get_backup_settings_sync()
        logger.info(f"Backup settings: enabled={db_settings['enabled']}")

        if not db_settings["enabled"]:
            logger.info("Scheduled backup skipped: backups disabled in settings")
            return {"success": False, "reason": "disabled"}

        logger.info("Starting scheduled backup...")

        from app.services.backup import BackupService
        service = BackupService()
        result = service.create_backup_sync(send_to_admin=True)

        if result.success:
            logger.info(f"Scheduled backup completed: {result.backup_key}")
            deleted = _cleanup_with_limits_sync(
                service,
                db_settings["retention_days"],
                db_settings["max_backups"]
            )
            if deleted:
                logger.info(f"Cleaned up {deleted} old backups")
        else:
            logger.error(f"Scheduled backup failed: {result.error}")

        return {"success": result.success, "key": result.backup_key}

    except Exception as e:
        tb_text = traceback.format_exc()
        logger.error(f"Scheduled backup task failed: {e}\n{tb_text}")

        # Уведомляем админа только при финальном retry
        if self.request.retries >= self.max_retries:
            try:
                from app.services.backup.notification import notify_backup_failure_sync
                notify_backup_failure_sync(
                    f"Scheduled backup task failed after {self.max_retries} retries: {e}",
                    traceback_text=tb_text
                )
            except Exception as notify_err:
                logger.error(f"Failed to send failure notification: {notify_err}")

        retry_delay = RETRY_DELAYS[min(self.request.retries, len(RETRY_DELAYS) - 1)]
        raise self.retry(exc=e, countdown=retry_delay)


@celery_app.task(name="app.tasks.backup_tasks.cleanup_old_backups", bind=True, max_retries=3, acks_late=True, soft_time_limit=120)
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

        from app.services.backup import BackupService
        service = BackupService()
        deleted = _cleanup_with_limits_sync(service, retention_days, max_backups)

        logger.info(f"Cleanup completed: {deleted} backups deleted")
        return {"deleted": deleted}

    except Exception as e:
        logger.exception("Backup cleanup failed")
        retry_delay = RETRY_DELAYS[min(self.request.retries, len(RETRY_DELAYS) - 1)]
        raise self.retry(exc=e, countdown=retry_delay)
