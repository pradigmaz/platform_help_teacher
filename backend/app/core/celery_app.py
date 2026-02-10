"""
Celery configuration
"""
import os
from celery import Celery
from celery.schedules import crontab

from app.core.time_constants import (
    CELERY_TASK_TIME_LIMIT_SECONDS,
    SCHEDULE_CHECK_INTERVAL_SECONDS,
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "edu_platform",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.schedule_tasks", "app.tasks.backup_tasks", "app.tasks.audit_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=CELERY_TASK_TIME_LIMIT_SECONDS,
    worker_prefetch_multiplier=1,
    # Redis scheduler вместо файлового (решает проблему Permission denied)
    beat_scheduler="celery.beat:PersistentScheduler",
    beat_schedule_filename="/tmp/celerybeat-schedule",
)

# Beat schedule for periodic tasks
# Время в Europe/Moscow (см. timezone выше)
celery_app.conf.beat_schedule = {
    "check-schedule-updates": {
        "task": "app.tasks.schedule_tasks.check_all_schedules",
        "schedule": float(SCHEDULE_CHECK_INTERVAL_SECONDS),
    },
    "create-daily-backup": {
        "task": "app.tasks.backup_tasks.create_scheduled_backup",
        "schedule": crontab(hour=20, minute=0),  # 20:00 МСК (17:00 UTC)
    },
    "cleanup-old-audit-logs": {
        "task": "app.tasks.audit_tasks.cleanup_old_audit_logs",
        "schedule": crontab(hour=4, minute=0),  # 04:00 МСК
    },
    "create-audit-partition": {
        "task": "app.tasks.audit_tasks.create_audit_partition",
        "schedule": crontab(hour=0, minute=5),  # 00:05 МСК
    },
}
