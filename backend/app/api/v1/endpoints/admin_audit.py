"""
Admin Audit API — просмотр логов действий студентов.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_active_superuser
from app.models.user import User
from app.audit.models import StudentAuditLog
from app.audit.schemas import AuditLogResponse, AuditLogListResponse, AuditStatsResponse
from app.audit.suspicion import enrich_logs_with_suspicion

router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
    user_id: Optional[UUID] = Query(None, description="Фильтр по студенту"),
    action_type: Optional[str] = Query(None, description="Фильтр по типу действия"),
    ip_address: Optional[str] = Query(None, description="Фильтр по IP"),
    date_from: Optional[datetime] = Query(None, description="Дата от"),
    date_to: Optional[datetime] = Query(None, description="Дата до"),
    path_contains: Optional[str] = Query(None, description="Поиск по пути"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Получить логи аудита с фильтрами."""
    query = select(StudentAuditLog).order_by(desc(StudentAuditLog.created_at))
    count_query = select(func.count(StudentAuditLog.id))
    
    # Применяем фильтры
    if user_id:
        query = query.where(StudentAuditLog.user_id == user_id)
        count_query = count_query.where(StudentAuditLog.user_id == user_id)
    
    if action_type:
        query = query.where(StudentAuditLog.action_type == action_type)
        count_query = count_query.where(StudentAuditLog.action_type == action_type)
    
    if ip_address:
        query = query.where(StudentAuditLog.ip_address.ilike(f"%{ip_address}%"))
        count_query = count_query.where(StudentAuditLog.ip_address.ilike(f"%{ip_address}%"))
    
    if date_from:
        query = query.where(StudentAuditLog.created_at >= date_from)
        count_query = count_query.where(StudentAuditLog.created_at >= date_from)
    
    if date_to:
        query = query.where(StudentAuditLog.created_at <= date_to)
        count_query = count_query.where(StudentAuditLog.created_at <= date_to)
    
    if path_contains:
        query = query.where(StudentAuditLog.path.ilike(f"%{path_contains}%"))
        count_query = count_query.where(StudentAuditLog.path.ilike(f"%{path_contains}%"))
    
    # Получаем общее количество
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Получаем записи
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Получаем имена пользователей
    user_ids = [log.user_id for log in logs if log.user_id]
    users_map = {}
    if user_ids:
        users_result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users_map = {u.id: u.full_name for u in users_result.scalars().all()}
    
    # Получаем подозрения для анонимных запросов
    suspicions = await enrich_logs_with_suspicion(db, list(logs))
    
    items = [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=users_map.get(log.user_id) if log.user_id else None,
            action_type=log.action_type,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            method=log.method,
            path=log.path,
            response_status=log.response_status,
            duration_ms=log.duration_ms,
            ip_address=log.ip_address,
            ip_forwarded=log.ip_forwarded,
            user_agent=log.user_agent,
            fingerprint=log.fingerprint,
            created_at=log.created_at,
            suspicion=suspicions.get(log.id).to_dict() if log.id in suspicions else None,
        )
        for log in logs
    ]
    
    return AuditLogListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log_detail(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
):
    """Получить детали записи аудита."""
    result = await db.execute(
        select(StudentAuditLog).where(StudentAuditLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    
    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    user_name = None
    if log.user_id:
        user = await db.get(User, log.user_id)
        user_name = user.full_name if user else None
    
    return AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        user_name=user_name,
        action_type=log.action_type,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        method=log.method,
        path=log.path,
        query_params=log.query_params,
        request_body=log.request_body,
        response_status=log.response_status,
        duration_ms=log.duration_ms,
        ip_address=log.ip_address,
        ip_forwarded=log.ip_forwarded,
        user_agent=log.user_agent,
        fingerprint=log.fingerprint,
        extra_data=log.extra_data,
        created_at=log.created_at,
    )


@router.get("/user/{user_id}", response_model=AuditLogListResponse)
async def get_user_audit_logs(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Получить логи конкретного пользователя."""
    return await get_audit_logs(
        db=db, _=_, user_id=user_id, skip=skip, limit=limit,
        action_type=None, ip_address=None, date_from=None, 
        date_to=None, path_contains=None
    )


@router.get("/stats/summary", response_model=AuditStatsResponse)
async def get_audit_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
    days: int = Query(7, ge=1, le=30),
):
    """Статистика аудита за период."""
    since = datetime.utcnow() - timedelta(days=days)
    
    # Общее количество
    total_result = await db.execute(
        select(func.count(StudentAuditLog.id))
        .where(StudentAuditLog.created_at >= since)
    )
    total = total_result.scalar() or 0
    
    # По типам действий
    actions_result = await db.execute(
        select(StudentAuditLog.action_type, func.count(StudentAuditLog.id))
        .where(StudentAuditLog.created_at >= since)
        .group_by(StudentAuditLog.action_type)
    )
    by_action = {row[0]: row[1] for row in actions_result.all()}
    
    # Уникальные пользователи
    users_result = await db.execute(
        select(func.count(func.distinct(StudentAuditLog.user_id)))
        .where(StudentAuditLog.created_at >= since)
        .where(StudentAuditLog.user_id.isnot(None))
    )
    unique_users = users_result.scalar() or 0
    
    # Уникальные IP
    ips_result = await db.execute(
        select(func.count(func.distinct(StudentAuditLog.ip_address)))
        .where(StudentAuditLog.created_at >= since)
    )
    unique_ips = ips_result.scalar() or 0
    
    return AuditStatsResponse(
        total_logs=total,
        unique_users=unique_users,
        unique_ips=unique_ips,
        by_action_type=by_action,
        period_days=days,
    )
