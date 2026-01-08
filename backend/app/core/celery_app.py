"""
Celery configuration
"""
import os
from celery import Celery

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
    task_time_limit=600,  # 10 min max
    worker_prefetch_multiplier=1,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "check-schedule-updates": {
        "task": "app.tasks.schedule_tasks.check_all_schedules",
        "schedule": 3600.0,  # Every hour
    },
    "create-daily-backup": {
        "task": "app.tasks.backup_tasks.create_scheduled_backup",
        "schedule": 86400.0,  # Every 24 hours
    },
    "cleanup-old-audit-logs": {
        "task": "app.tasks.audit_tasks.cleanup_old_audit_logs",
        "schedule": 86400.0,  # Every 24 hours
    },
    "create-audit-partition": {
        "task": "app.tasks.audit_tasks.create_audit_partition",
        "schedule": 86400.0,  # Every 24 hours
    },
}
