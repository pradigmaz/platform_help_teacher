"""
Admin Audit Export API — выгрузка логов для анализа ИИ.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_superuser
from app.models.user import User
from app.audit.models import StudentAuditLog

router = APIRouter()


async def _stream_jsonl(db: AsyncSession, query, users_map: dict):
    """Генератор JSONL строк."""
    import json
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    for log in logs:
        record = {
            "id": str(log.id),
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "user_id": str(log.user_id) if log.user_id else None,
            "user_name": users_map.get(log.user_id) if log.user_id else None,
            "action": log.action_type,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "method": log.method,
            "path": log.path,
            "query_params": log.query_params,
            "request_body": log.request_body,
            "status": log.response_status,
            "duration_ms": log.duration_ms,
            "ip": log.ip_address,
            "ip_chain": log.ip_forwarded,
            "user_agent": log.user_agent,
            "fingerprint": log.fingerprint,
            "extra": log.extra_data,
        }
        yield json.dumps(record, ensure_ascii=False) + "\n"


@router.get("/export")
async def export_audit_logs(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
    user_id: Optional[UUID] = Query(None, description="Фильтр по студенту"),
    action_type: Optional[str] = Query(None, description="Фильтр по типу действия"),
    date_from: Optional[datetime] = Query(None, description="Дата от"),
    date_to: Optional[datetime] = Query(None, description="Дата до"),
    days: int = Query(7, ge=1, le=90, description="Период в днях (если date_from не указан)"),
    limit: int = Query(10000, ge=1, le=100000, description="Макс. записей"),
):
    """
    Экспорт логов в JSONL формате для анализа ИИ.
    
    Формат: одна JSON-строка на запись, разделённые \\n.
    Удобно для потоковой обработки и скармливания LLM.
    """
    # Базовый запрос
    query = select(StudentAuditLog).order_by(desc(StudentAuditLog.created_at))
    
    # Фильтры
    if user_id:
        query = query.where(StudentAuditLog.user_id == user_id)
    
    if action_type:
        query = query.where(StudentAuditLog.action_type == action_type)
    
    if date_from:
        query = query.where(StudentAuditLog.created_at >= date_from)
    else:
        since = datetime.utcnow() - timedelta(days=days)
        query = query.where(StudentAuditLog.created_at >= since)
    
    if date_to:
        query = query.where(StudentAuditLog.created_at <= date_to)
    
    query = query.limit(limit)
    
    # Предзагрузка пользователей
    result = await db.execute(query)
    logs = result.scalars().all()
    
    user_ids = list({log.user_id for log in logs if log.user_id})
    users_map = {}
    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users_map = {u.id: u.full_name for u in users_result.scalars().all()}
    
    # Генерируем JSONL
    import json
    
    def generate():
        for log in logs:
            record = {
                "id": str(log.id),
                "ts": log.created_at.isoformat() if log.created_at else None,
                "user_id": str(log.user_id) if log.user_id else None,
                "user": users_map.get(log.user_id),
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
                "ua": log.user_agent,
                "fp": log.fingerprint,
                "extra": log.extra_data,
            }
            yield json.dumps(record, ensure_ascii=False) + "\n"
    
    filename = f"audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jsonl"
    
    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
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
        db=db, _=_, user_id=user_id, days=days, limit=limit,
        action_type=None, date_from=None, date_to=None
    )
