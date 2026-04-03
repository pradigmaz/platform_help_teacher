"""
Admin Audit API — просмотр логов действий студентов.
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser, get_db
from app.audit.models import StudentAuditLog
from app.audit.schemas import AuditLogListResponse, AuditLogResponse, AuditStatsResponse
from app.audit.suspicion import enrich_logs_with_suspicion
from app.core import error_messages as em
from app.core.limiter import limiter
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
@limiter.limit("30/minute")
async def get_audit_logs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
    user_id: UUID | None = Query(None, description="Фильтр по студенту"),
    action_type: str | None = Query(None, description="Фильтр по типу действия"),
    ip_address: str | None = Query(None, description="Фильтр по IP"),
    date_from: datetime | None = Query(None, description="Дата от"),
    date_to: datetime | None = Query(None, description="Дата до"),
    path_contains: str | None = Query(None, description="Поиск по пути"),
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
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users_map = {u.id: u.full_name for u in users_result.scalars().all()}

    # Получаем подозрения для анонимных запросов
    suspicions = await enrich_logs_with_suspicion(db, list(logs))

    items = [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=users_map.get(log.user_id) if log.user_id else None,
            actor_role=log.actor_role,
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
                suspicion=suspicions[log.id].to_dict() if log.id in suspicions and suspicions[log.id] is not None else None,
        )
        for log in logs
    ]

    return AuditLogListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{log_id}", response_model=AuditLogResponse)
@limiter.limit("60/minute")
async def get_audit_log_detail(
    request: Request,
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
):
    """Получить детали записи аудита."""
    result = await db.execute(select(StudentAuditLog).where(StudentAuditLog.id == log_id))
    log = result.scalar_one_or_none()

    if not log:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=em.AUDIT_LOG_NOT_FOUND)

    user_name = None
    if log.user_id:
        user = await db.get(User, log.user_id)
        user_name = user.full_name if user else None

    return AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        user_name=user_name,
        actor_role=log.actor_role,
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
@limiter.limit("30/minute")
async def get_user_audit_logs(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Получить логи конкретного пользователя."""
    return await get_audit_logs(
        request=request,
        db=db,
        _=_,
        user_id=user_id,
        skip=skip,
        limit=limit,
        action_type=None,
        ip_address=None,
        date_from=None,
        date_to=None,
        path_contains=None,
    )


@router.get("/stats/summary", response_model=AuditStatsResponse)
@limiter.limit("10/minute")
async def get_audit_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
    days: int = Query(7, ge=1, le=30),
):
    """Статистика аудита за период."""
    since = datetime.now(UTC) - timedelta(days=days)

    # Общее количество
    total_result = await db.execute(select(func.count(StudentAuditLog.id)).where(StudentAuditLog.created_at >= since))
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
        select(func.count(func.distinct(StudentAuditLog.ip_address))).where(StudentAuditLog.created_at >= since)
    )
    unique_ips = ips_result.scalar() or 0

    return AuditStatsResponse(
        total_logs=total,
        unique_users=unique_users,
        unique_ips=unique_ips,
        by_action_type=by_action,
        period_days=days,
    )


def _build_delete_filters(
    date_from: datetime | None,
    date_to: datetime | None,
    status_codes: list[int] | None,
    action_type: str | None,
):
    """Построить фильтры для удаления/подсчёта логов."""
    filters = []

    if date_from:
        filters.append(StudentAuditLog.created_at >= date_from)
    if date_to:
        filters.append(StudentAuditLog.created_at <= date_to)
    if status_codes:
        filters.append(StudentAuditLog.response_status.in_(status_codes))
    if action_type:
        filters.append(StudentAuditLog.action_type == action_type)

    return filters


@router.get("/clear/preview")
@limiter.limit("10/minute")
async def preview_clear_logs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
    date_from: datetime | None = Query(None, description="Дата от"),
    date_to: datetime | None = Query(None, description="Дата до"),
    status_codes: str | None = Query(None, description="Статус коды через запятую (401,404,500)"),
    action_type: str | None = Query(None, description="Тип действия"),
):
    """Предпросмотр: сколько записей будет удалено."""
    # Парсим статус коды
    codes_list = None
    if status_codes:
        try:
            codes_list = [int(c.strip()) for c in status_codes.split(",") if c.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status_codes format")

    filters = _build_delete_filters(date_from, date_to, codes_list, action_type)

    if not filters:
        raise HTTPException(status_code=400, detail="At least one filter is required")

    # Подсчёт записей
    count_query = select(func.count(StudentAuditLog.id))
    for f in filters:
        count_query = count_query.where(f)

    result = await db.execute(count_query)
    count = result.scalar() or 0

    # Статистика по статус кодам
    stats_query = select(StudentAuditLog.response_status, func.count(StudentAuditLog.id)).group_by(
        StudentAuditLog.response_status
    )
    for f in filters:
        stats_query = stats_query.where(f)

    stats_result = await db.execute(stats_query)
    by_status = {str(row[0] or "null"): row[1] for row in stats_result.all()}

    return {
        "count": count,
        "by_status": by_status,
        "filters": {
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "status_codes": codes_list,
            "action_type": action_type,
        },
    }


@router.delete("/clear")
@limiter.limit("5/minute")
async def clear_logs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
    date_from: datetime | None = Query(None, description="Дата от"),
    date_to: datetime | None = Query(None, description="Дата до"),
    status_codes: str | None = Query(None, description="Статус коды через запятую (401,404,500)"),
    action_type: str | None = Query(None, description="Тип действия"),
    confirm: bool = Query(False, description="Подтверждение удаления"),
):
    """Удалить логи по фильтрам."""
    if not confirm:
        raise HTTPException(status_code=400, detail=em.CONFIRMATION_REQUIRED)

    # Парсим статус коды
    codes_list = None
    if status_codes:
        try:
            codes_list = [int(c.strip()) for c in status_codes.split(",") if c.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail=em.INVALID_STATUS_CODES_FORMAT)

    filters = _build_delete_filters(date_from, date_to, codes_list, action_type)

    if not filters:
        raise HTTPException(status_code=400, detail=em.AT_LEAST_ONE_FILTER_REQUIRED)

    # Подсчёт перед удалением
    count_query = select(func.count(StudentAuditLog.id))
    for f in filters:
        count_query = count_query.where(f)

    count_result = await db.execute(count_query)
    count = count_result.scalar() or 0

    if count == 0:
        return {"deleted": 0, "message": "No logs matched the filters"}

    # Удаление
    delete_query = delete(StudentAuditLog)
    for f in filters:
        delete_query = delete_query.where(f)

    await db.execute(delete_query)
    await db.commit()

    # Логируем операцию
    logger.warning(
        f"Audit logs cleared | admin={admin.id} ({admin.full_name}) | "
        f"count={count} | date_from={date_from} | date_to={date_to} | "
        f"status_codes={codes_list} | action_type={action_type}"
    )

    return {
        "deleted": count,
        "message": f"Successfully deleted {count} audit logs",
        "filters": {
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "status_codes": codes_list,
            "action_type": action_type,
        },
    }
