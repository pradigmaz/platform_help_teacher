"""
Сервис аудита — асинхронная и синхронная запись в БД.
"""
import logging
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from .models import StudentAuditLog
from .schemas import AuditContext, AuditLogCreate
from .constants import SECURITY_CRITICAL_ACTIONS

logger = logging.getLogger(__name__)

# Fallback logger for failed audit writes (security-critical)
audit_fallback_logger = logging.getLogger("audit.fallback")


class AuditService:
    """Сервис для записи аудит-логов."""
    
    MAX_RETRIES = 3
    
    async def write_log(self, context: AuditContext) -> None:
        """
        Асинхронная запись лога в БД.
        Fire-and-forget: ошибки логируются, но не пробрасываются.
        """
        try:
            async with AsyncSessionLocal() as db:
                log_entry = self._create_log_entry(context)
                db.add(log_entry)
                await db.commit()
        except Exception as e:
            # Тихо логируем ошибку, не ломаем основной flow
            logger.error(f"Audit write failed: {e}", exc_info=True)
            self._write_fallback(context, str(e))
    
    async def write_log_sync(self, context: AuditContext) -> bool:
        """
        Синхронная запись с retry для security-critical событий.
        Returns True если запись успешна.
        """
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                async with AsyncSessionLocal() as db:
                    log_entry = self._create_log_entry(context)
                    db.add(log_entry)
                    await db.commit()
                    return True
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Audit sync write attempt {attempt + 1}/{self.MAX_RETRIES} failed: {e}"
                )
        
        # Все попытки исчерпаны — пишем в fallback
        logger.error(f"Audit sync write failed after {self.MAX_RETRIES} attempts: {last_error}")
        self._write_fallback(context, str(last_error))
        return False
    
    def _create_log_entry(self, context: AuditContext) -> StudentAuditLog:
        """Создать объект записи лога."""
        return StudentAuditLog(
            id=uuid4(),
            user_id=context.user_id,
            session_id=context.session_id,
            correlation_id=context.correlation_id,
            actor_role=context.actor_role,
            action_type=context.action_type,
            entity_type=context.entity_type,
            entity_id=context.entity_id,
            method=context.method,
            path=context.path,
            query_params=context.query_params,
            request_body=context.request_body,
            response_status=context.response_status,
            duration_ms=context.duration_ms,
            ip_address=context.ip_address,
            ip_forwarded=context.ip_forwarded,
            user_agent=context.user_agent,
            fingerprint=context.fingerprint,
            extra_data=context.extra_data,
        )
    
    def _write_fallback(self, context: AuditContext, error: str) -> None:
        """Записать в fallback лог при ошибке БД."""
        audit_fallback_logger.error(
            f"AUDIT_FALLBACK | action={context.action_type} | "
            f"user_id={context.user_id} | ip={context.ip_address} | "
            f"path={context.path} | error={error}"
        )
    
    async def write_from_schema(self, data: AuditLogCreate) -> None:
        """Запись из Pydantic схемы."""
        context = AuditContext(
            request_id=str(uuid4()),
            **data.model_dump()
        )
        await self.write_log(context)
    
    def is_security_critical(self, action_type: str) -> bool:
        """Проверить, является ли действие security-critical."""
        return action_type in SECURITY_CRITICAL_ACTIONS


# Singleton instance
_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """Получить singleton экземпляр сервиса."""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
