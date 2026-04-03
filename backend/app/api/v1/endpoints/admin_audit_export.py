"""
Admin Audit Export API — выгрузка логов для анализа ИИ.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser, get_db
from app.audit.models import StudentAuditLog
from app.models.user import User

router = APIRouter()
EXPORT_BATCH_SIZE = 500


async def _load_users_map(db: AsyncSession, logs: list[StudentAuditLog]) -> dict:
    user_ids = list({log.user_id for log in logs if log.user_id})
    if not user_ids:
        return {}

    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    return {user.id: user.full_name for user in users_result.scalars().all()}


@router.get("/export")
async def export_audit_logs(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
    user_id: UUID | None = Query(None, description="Фильтр по студенту"),
    action_type: str | None = Query(None, description="Фильтр по типу действия"),
    date_from: datetime | None = Query(None, description="Дата от"),
    date_to: datetime | None = Query(None, description="Дата до"),
    days: int = Query(7, ge=1, le=90, description="Период в днях (если date_from не указан)"),
    limit: int = Query(10000, ge=1, le=100000, description="Макс. записей"),
):
    """
    Экспорт логов в JSONL формате для анализа ИИ.

    Формат: одна JSON-строка на запись, разделённые \\n.
    Удобно для потоковой обработки и скармливания LLM.
    """
    # Базовый запрос
    query = select(StudentAuditLog).order_by(desc(StudentAuditLog.created_at), desc(StudentAuditLog.id))

    # Фильтры
    if user_id:
        query = query.where(StudentAuditLog.user_id == user_id)

    if action_type:
        query = query.where(StudentAuditLog.action_type == action_type)

    if date_from:
        query = query.where(StudentAuditLog.created_at >= date_from)
    else:
        since = datetime.now(UTC) - timedelta(days=days)
        query = query.where(StudentAuditLog.created_at >= since)

    if date_to:
        query = query.where(StudentAuditLog.created_at <= date_to)

    # Генерируем JSONL
    import json

    async def generate():
        emitted = 0

        while emitted < limit:
            batch_limit = min(EXPORT_BATCH_SIZE, limit - emitted)
            result = await db.execute(query.offset(emitted).limit(batch_limit))
            logs = result.scalars().all()
            if not logs:
                break

            users_map = await _load_users_map(db, list(logs))

            for log in logs:
                record = {
                    "id": str(log.id),
                    "ts": log.created_at.isoformat() if log.created_at else None,
                    "user_id": str(log.user_id) if log.user_id else None,
                    "user": users_map.get(log.user_id),
                    "actor_role": log.actor_role,
                    "action": log.action_type,
                    "entity": log.entity_type,
                    "entity_id": str(log.entity_id) if log.entity_id else None,
                    "method": log.method,
                    "path": log.path,
                    "params": log.query_params,
                    "body": log.request_body,
                    "status": log.response_status,
                    "ms": log.duration_ms,
                    "ip": log.ip_address,
                    "ip_chain": log.ip_forwarded,
                    "ua": log.user_agent,
                    "fp": log.fingerprint,
                    "extra": log.extra_data,
                }
                yield json.dumps(record, ensure_ascii=False) + "\n"

            emitted += len(logs)
            if len(logs) < batch_limit:
                break

    filename = f"audit_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.jsonl"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/user/{user_id}")
async def export_user_audit_logs(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10000, ge=1, le=100000),
):
    """Экспорт логов конкретного пользователя."""
    return await export_audit_logs(
        db=db, _=_, user_id=user_id, days=days, limit=limit, action_type=None, date_from=None, date_to=None
    )
