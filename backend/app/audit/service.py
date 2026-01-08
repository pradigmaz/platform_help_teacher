"""
Сервис аудита — асинхронная запись в БД.
"""
import logging
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from .models import StudentAuditLog
from .schemas import AuditContext, AuditLogCreate

logger = logging.getLogger(__name__)


class AuditService:
    """Сервис для записи аудит-логов."""
    
    async def write_log(self, context: AuditContext) -> None:
        """
        Асинхронная запись лога в БД.
        Fire-and-forget: ошибки логируются, но не пробрасываются.
        """
        try:
            async with AsyncSessionLocal() as db:
                log_entry = StudentAuditLog(
                    id=uuid4(),
                    user_id=context.user_id,
                    session_id=context.session_id,
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
                db.add(log_entry)
                await db.commit()
        except Exception as e:
            # Тихо логируем ошибку, не ломаем основной flow
            logger.error(f"Audit write failed: {e}", exc_info=True)
    
    async def write_from_schema(self, data: AuditLogCreate) -> None:
        """Запись из Pydantic схемы."""
        context = AuditContext(
            request_id=str(uuid4()),
            **data.model_dump()
        )
        await self.write_log(context)


# Singleton instance
_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """Получить singleton экземпляр сервиса."""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
