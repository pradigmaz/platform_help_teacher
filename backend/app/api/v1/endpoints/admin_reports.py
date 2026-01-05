"""
Admin API endpoints для управления публичными отчётами.

Требует авторизации преподавателя или администратора.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.core.limiter import limiter
from app.core.config import settings
from app.models import User, Group
from app.models.group_report import GroupReport, ReportType
from app.crud.crud_report import crud_report
from app.schemas.report import (
    ReportCreate,
    ReportUpdate,
    ReportResponse,
    ReportListResponse,
    ReportViewsResponse,
    ReportViewStats,
    ReportViewRecord,
)
from app.services.reports import ReportService

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_report_url(code: str) -> str:
    """Построить полный URL отчёта."""
    base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    return f"{base_url}/report/{code}"


async def _report_to_response(report: GroupReport, db: AsyncSession) -> ReportResponse:
    """Преобразовать модель отчёта в схему ответа."""
    # Получаем группу для group_code и group_name
    group = report.group
    group_code = group.code if group else "N/A"
    group_name = group.name if group else None
    
    return ReportResponse(
        id=report.id,
        code=report.code,
        group_id=report.group_id,
        group_code=group_code,
        group_name=group_name,
        report_type=ReportType(report.report_type),
        expires_at=report.expires_at,
        has_pin=report.pin_hash is not None,
        show_names=report.show_names,
        show_grades=report.show_grades,
        show_attendance=report.show_attendance,
        show_notes=report.show_notes,
        show_rating=report.show_rating,
        is_active=report.is_active,
        views_count=report.views_count,
        last_viewed_at=report.last_viewed_at,
        created_at=report.created_at,
        url=_build_report_url(report.code),
    )


async def _get_report_or_404(
    db: AsyncSession,
    report_id: UUID,
    current_user: User
) -> GroupReport:
    """Получить отчёт по ID или вернуть 404."""
    report = await crud_report.get_by_id(db, report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Проверка владельца (только создатель или админ)
    if report.created_by != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report"
        )
    
    return report


@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_report(
    request: Request,
    report_in: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
):
    """
    Создать новый публичный отчёт для группы.
    
    - **group_id**: ID группы
    - **report_type**: Тип отчёта (full, attestation_only, attendance_only)
    - **expires_in_days**: Срок действия в днях (null = бессрочно)
    - **pin_code**: PIN-код для защиты (4-6 цифр, опционально)
    - **show_***: Настройки видимости данных
    """
    # Проверяем существование группы
    result = await db.execute(select(Group).where(Group.id == report_in.group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Создаём отчёт
    report = await crud_report.create(
        db,
        group_id=report_in.group_id,
        created_by=current_user.id,
        report_type=report_in.report_type,
        expires_in_days=report_in.expires_in_days,
        pin_code=report_in.pin_code,
        show_names=report_in.show_names,
        show_grades=report_in.show_grades,
        show_attendance=report_in.show_attendance,
        show_notes=report_in.show_notes,
        show_rating=report_in.show_rating,
    )
    
    logger.info(f"Teacher {current_user.id} created report {report.code} for group {group.code}")
    
    return await _report_to_response(report, db)


@router.get("/reports", response_model=ReportListResponse)
async def list_reports(
    group_id: Optional[UUID] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
):
    """
    Получить список отчётов текущего преподавателя.
    
    - **group_id**: Фильтр по группе (опционально)
    - **include_inactive**: Включать деактивированные отчёты
    """
    if group_id:
        reports = await crud_report.get_by_group(
            db, 
            group_id, 
            include_inactive=include_inactive
        )
        # Фильтруем по создателю (если не админ)
        if current_user.role.value != "admin":
            reports = [r for r in reports if r.created_by == current_user.id]
    else:
        reports = await crud_report.get_by_teacher(
            db, 
            current_user.id, 
            include_inactive=include_inactive
        )
    
    response_reports = [await _report_to_response(r, db) for r in reports]
    
    return ReportListResponse(
        reports=response_reports,
        total=len(response_reports)
    )


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
):
    """
    Получить детали отчёта по ID.
    """
    report = await _get_report_or_404(db, report_id, current_user)
    return await _report_to_response(report, db)


@router.put("/reports/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: UUID,
    report_in: ReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
):
    """
    Обновить настройки отчёта.
    
    - **expires_in_days**: Новый срок действия
    - **pin_code**: Новый PIN-код
    - **remove_pin**: Удалить PIN-защиту
    - **show_***: Настройки видимости
    - **is_active**: Статус активности
    """
    report = await _get_report_or_404(db, report_id, current_user)
    
    updated_report = await crud_report.update(
        db,
        report,
        expires_in_days=report_in.expires_in_days,
        pin_code=report_in.pin_code,
        remove_pin=report_in.remove_pin,
        show_names=report_in.show_names,
        show_grades=report_in.show_grades,
        show_attendance=report_in.show_attendance,
        show_notes=report_in.show_notes,
        show_rating=report_in.show_rating,
        is_active=report_in.is_active,
    )
    
    logger.info(f"Teacher {current_user.id} updated report {report.code}")
    
    return await _report_to_response(updated_report, db)


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def deactivate_report(
    request: Request,
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
):
    """
    Деактивировать отчёт.
    
    Отчёт не удаляется физически, а помечается как неактивный.
    Доступ по ссылке будет заблокирован.
    """
    report = await _get_report_or_404(db, report_id, current_user)
    
    await crud_report.deactivate(db, report)
    
    logger.info(f"Teacher {current_user.id} deactivated report {report.code}")
    
    return None


@router.post("/reports/{report_id}/regenerate", response_model=ReportResponse)
@limiter.limit("10/minute")
async def regenerate_report_code(
    request: Request,
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
):
    """
    Сгенерировать новый код для отчёта.
    
    Старый код становится недействительным.
    Полезно если ссылка была скомпрометирована.
    """
    report = await _get_report_or_404(db, report_id, current_user)
    
    old_code = report.code
    updated_report = await crud_report.regenerate_code(db, report)
    
    logger.info(
        f"Teacher {current_user.id} regenerated code for report: "
        f"{old_code} -> {updated_report.code}"
    )
    
    return await _report_to_response(updated_report, db)


@router.get("/reports/{report_id}/views", response_model=ReportViewsResponse)
async def get_report_views(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
):
    """
    Получить статистику просмотров отчёта.
    
    Возвращает:
    - Общее количество просмотров
    - Количество уникальных IP
    - Дату последнего просмотра
    - Просмотры по датам
    - Последние 50 просмотров с деталями
    """
    report = await _get_report_or_404(db, report_id, current_user)
    
    service = ReportService(db)
    
    stats = await service.get_view_stats(report.id)
    recent_views = await service.get_recent_views(report.id, limit=50)
    
    return ReportViewsResponse(
        report_id=report.id,
        stats=stats,
        recent_views=recent_views,
    )
