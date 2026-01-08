"""
Celery tasks для обслуживания аудит-логов.
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import delete, select, func

from app.core.celery_app import celery_app
from app.db.session import SyncSessionLocal
from app.audit.models import StudentAuditLog

logger = logging.getLogger(__name__)

# Retention period in days (configurable via settings)
AUDIT_RETENTION_DAYS = 365


@celery_app.task(name="app.tasks.audit_tasks.cleanup_old_audit_logs")
def cleanup_old_audit_logs(retention_days: int = AUDIT_RETENTION_DAYS) -> dict:
    """
    Удаляет аудит-логи старше retention_days.
    
    GDPR compliance: право на забвение.
    Performance: предотвращает неограниченный рост таблицы.
    
    Рекомендуется запускать ежедневно через Celery Beat.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    with SyncSessionLocal() as db:
        try:
            # Считаем количество записей для удаления
            count_query = select(func.count(StudentAuditLog.id)).where(
                StudentAuditLog.created_at < cutoff_date
            )
            result = db.execute(count_query)
            count = result.scalar() or 0
            
            if count == 0:
                logger.info(f"No audit logs older than {retention_days} days to delete")
                return {"deleted": 0, "cutoff_date": cutoff_date.isoformat()}
            
            # Удаляем батчами для избежания блокировок
            batch_size = 10000
            total_deleted = 0
            
            while True:
                # Удаляем батч
                delete_query = delete(StudentAuditLog).where(
                    StudentAuditLog.id.in_(
                        select(StudentAuditLog.id)
                        .where(StudentAuditLog.created_at < cutoff_date)
                        .limit(batch_size)
                    )
                )
                result = db.execute(delete_query)
                deleted = result.rowcount
                db.commit()
                
                total_deleted += deleted
                
                if deleted < batch_size:
                    break
                
                logger.info(f"Deleted {total_deleted} audit logs so far...")
            
            logger.info(f"Audit cleanup complete: deleted {total_deleted} logs older than {cutoff_date}")
            return {
                "deleted": total_deleted,
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": retention_days
            }
            
        except Exception as e:
            logger.error(f"Audit cleanup failed: {e}", exc_info=True)
            db.rollback()
            raise


@celery_app.task(name="app.tasks.audit_tasks.create_audit_partition")
def create_audit_partition() -> dict:
    """
    Создаёт партицию на следующий месяц если её нет.
    
    Рекомендуется запускать ежедневно через Celery Beat.
    """
    with SyncSessionLocal() as db:
        try:
            db.execute("SELECT create_audit_partition_if_needed()")
            db.commit()
            logger.info("Audit partition check complete")
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Audit partition creation failed: {e}", exc_info=True)
            db.rollback()
            raise
