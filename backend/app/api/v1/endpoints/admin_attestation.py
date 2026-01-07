from typing import Any, List, Dict, Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.core.limiter import limiter
from app.models import User, Group, AttestationSettings, AttestationType
from app.services.attestation_service import AttestationService
from app.services.attestation.audit import AttestationAuditService
from app.schemas.attestation import (
    AttestationSettingsResponse,
    AttestationSettingsUpdate,
    AttestationResult,
    AttestationResultResponse,
    GroupAttestationResponse,
    AttestationType as AttestationTypeSchema,
)

router = APIRouter()

# ============== Attestation Settings Endpoints ==============
# Requirements: 5.1, 5.2, 5.4, 5.5
# Глобальные настройки аттестации (применяются ко всем группам)

@router.get("/attestation/grade-scale/{attestation_type}")
async def get_grade_scale(
    attestation_type: AttestationTypeSchema,
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Получить шкалу оценок для типа аттестации.
    
    Returns:
        Dict со шкалой оценок (неуд/уд/хор/отл -> диапазоны баллов)
    """
    return AttestationSettings.get_grade_scale(attestation_type)


@router.post("/attestation/settings/initialize", response_model=Dict[str, AttestationSettingsResponse])
async def initialize_attestation_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Инициализировать глобальные настройки аттестации.
    
    Создаёт настройки по умолчанию для обоих типов аттестации (первая и вторая).
    Если настройки уже существуют, возвращает существующие.
    
    Requirements: 1.7, 1.8, 1.9, 1.10, 1.11 - настройки по умолчанию
    
    Returns:
        Dict с настройками для first и second аттестации
    """
    service = AttestationService(db)
    
    first_settings, second_settings = await service.initialize_settings()
    
    return {
        "first": service.to_response(first_settings),
        "second": service.to_response(second_settings)
    }


@router.get("/attestation/settings/{attestation_type}", response_model=AttestationSettingsResponse)
async def get_attestation_settings(
    attestation_type: AttestationTypeSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Получить глобальные настройки аттестации.
    
    Requirements: 5.1 - GET endpoint to retrieve current attestation settings
    Requirements: 5.5 - require teacher authentication
    
    Args:
        attestation_type: Тип аттестации (first/second)
    
    Returns:
        AttestationSettingsResponse с текущими настройками
    """
    service = AttestationService(db)
    
    # Конвертируем тип из схемы в модель
    model_type = attestation_type
    
    settings = await service.get_or_create_settings(model_type)
    return service.to_response(settings)


@router.put("/attestation/settings", response_model=AttestationSettingsResponse)
@limiter.limit("5/minute")
async def update_attestation_settings(
    request: Request,
    settings_in: AttestationSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Обновить глобальные настройки аттестации.
    
    Requirements: 5.2 - PUT endpoint to update attestation settings
    Requirements: 5.3 - validate all parameters (через Pydantic схему)
    Requirements: 5.4 - return appropriate HTTP status codes
    Requirements: 5.5 - require teacher authentication
    
    Args:
        settings_in: Новые настройки аттестации
    
    Returns:
        AttestationSettingsResponse с обновлёнными настройками
    
    Raises:
        400: Если веса компонентов не суммируются в 100%
    """
    service = AttestationService(db)
    audit_service = AttestationAuditService(db)
    
    # Получаем старые настройки для audit log
    old_settings = await service.get_settings(settings_in.attestation_type)
    
    try:
        settings = await service.update_settings(settings_in)
        
        # Логируем изменение
        ip_address = request.client.host if request.client else None
        await audit_service.log_settings_change(
            attestation_type=settings_in.attestation_type,
            action="update" if old_settings else "create",
            old_settings=old_settings,
            new_settings=settings,
            changed_by_id=current_user.id,
            ip_address=ip_address
        )
        await db.commit()
        
        return service.to_response(settings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Attestation Calculation Endpoints ==============
# Requirements: 6.1, 6.2, 6.3

@router.get("/attestation/calculate/{student_id}/{attestation_type}", response_model=AttestationResultResponse)
@limiter.limit("30/minute")
async def calculate_student_attestation(
    request: Request,
    student_id: UUID,
    attestation_type: AttestationTypeSchema,
    activity_points: float = Query(default=0.0, ge=0, description="Баллы за активность"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Рассчитать баллы аттестации для студента.
    
    Requirements: 6.1 - endpoint to calculate score for individual student
    Requirements: 6.3 - return detailed breakdown by components
    
    Args:
        student_id: ID студента
        attestation_type: Тип аттестации (first/second)
        activity_points: Дополнительные баллы за активность
    
    Returns:
        AttestationResultResponse с детализацией расчёта
    
    Raises:
        404: Если студент не найден или не состоит в группе
    """
    # Получаем студента
    student_result = await db.execute(select(User).where(User.id == student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    
    if not student.group_id:
        raise HTTPException(status_code=400, detail="Студент не состоит в группе")
    
    service = AttestationService(db)
    
    # Конвертируем тип
    model_type = attestation_type
    
    try:
        result = await service.calculate_student_score(
            student_id=student_id,
            group_id=student.group_id,
            attestation_type=model_type,
            activity_points=activity_points
        )
        
        return AttestationResultResponse(
            student_id=result.student_id,
            student_name=result.student_name,
            attestation_type=attestation_type,
            total_score=result.total_score,
            lab_score=result.lab_score,
            attendance_score=result.attendance_score,
            activity_score=result.activity_score,
            grade=result.grade,
            is_passing=result.is_passing,
            max_points=result.max_points,
            min_passing_points=result.min_passing_points,
            components_breakdown=result.components_breakdown,
            calculated_at=datetime.now(timezone.utc)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/attestation/calculate/group/{group_id}/{attestation_type}", response_model=GroupAttestationResponse)
@limiter.limit("10/minute")
async def calculate_group_attestation(
    request: Request,
    group_id: UUID,
    attestation_type: AttestationTypeSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Рассчитать баллы аттестации для всей группы.
    
    Requirements: 6.2 - endpoint to calculate scores for entire group
    Requirements: 6.3 - return detailed breakdown by components
    
    Args:
        group_id: ID группы
        attestation_type: Тип аттестации (first/second)
    
    Returns:
        GroupAttestationResponse со всеми студентами и статистикой
    
    Raises:
        404: Если группа не найдена
    """
    # Проверяем существование группы
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    # Получаем всех студентов группы
    from app.models import UserRole
    students_result = await db.execute(
        select(User).where(
            User.group_id == group_id,
            User.role == UserRole.STUDENT,
            User.is_active == True
        )
    )
    students = students_result.scalars().all()
    
    if not students:
        raise HTTPException(status_code=404, detail="В группе нет активных студентов")
    
    service = AttestationService(db)
    model_type = attestation_type
    
    # Рассчитываем баллы для всей группы пакетно
    results, errors = await service.calculate_group_scores_batch(
        group_id=group_id,
        attestation_type=model_type,
        students=students
    )
    
    # Статистика
    passing_students = sum(1 for r in results if r.is_passing)
    failing_students = len(results) - passing_students
    
    # Распределение по оценкам
    grade_distribution: Dict[str, int] = {"неуд": 0, "уд": 0, "хор": 0, "отл": 0}
    for r in results:
        if r.grade in grade_distribution:
            grade_distribution[r.grade] += 1
    
    # Средний балл
    average_score = sum(r.total_score for r in results) / len(results) if results else 0.0
    
    return GroupAttestationResponse(
        group_id=group_id,
        group_code=group.code,
        attestation_type=attestation_type,
        calculated_at=datetime.now(timezone.utc),
        total_students=len(results),
        passing_students=passing_students,
        failing_students=failing_students,
        grade_distribution=grade_distribution,
        average_score=round(average_score, 2),
        students=results,
        errors=errors
    )


# ============== All Students Attestation Endpoint ==============
# Requirements: 1.1, 1.2 - страница баллов аттестации для всех студентов

@router.get("/attestation/scores/all/{attestation_type}", response_model=GroupAttestationResponse)
@limiter.limit("5/minute")
async def calculate_all_students_attestation(
    request: Request,
    attestation_type: AttestationTypeSchema,
    skip: int = Query(default=0, ge=0, description="Пропустить записей"),
    limit: int = Query(default=100, ge=1, le=500, description="Лимит записей (макс 500)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Рассчитать баллы аттестации для ВСЕХ студентов (все группы).
    
    Requirements: 1.1 - страница баллов аттестации
    Requirements: 1.2 - отображение ФИО, баллов, оценки
    
    Студенты сортируются по ФИО (А-Я).
    Каждый студент содержит group_code для отображения группы.
    Поддерживает пагинацию для больших наборов данных.
    
    Args:
        attestation_type: Тип аттестации (first/second)
        skip: Пропустить записей (для пагинации)
        limit: Лимит записей (макс 500)
    
    Returns:
        GroupAttestationResponse со студентами и статистикой
    """
    service = AttestationService(db)
    model_type = attestation_type
    
    # Рассчитываем баллы для всех студентов
    all_results, errors = await service.calculate_all_students_scores(
        attestation_type=model_type
    )
    
    if not all_results:
        raise HTTPException(status_code=404, detail="Нет активных студентов")
    
    # Статистика по ВСЕМ студентам (до пагинации)
    total_count = len(all_results)
    passing_students = sum(1 for r in all_results if r.is_passing)
    failing_students = total_count - passing_students
    
    # Распределение по оценкам (по всем)
    grade_distribution: Dict[str, int] = {"неуд": 0, "уд": 0, "хор": 0, "отл": 0}
    for r in all_results:
        if r.grade in grade_distribution:
            grade_distribution[r.grade] += 1
    
    # Средний балл (по всем)
    average_score = sum(r.total_score for r in all_results) / total_count if total_count else 0.0
    
    # Применяем пагинацию
    paginated_results = all_results[skip:skip + limit]
    
    return GroupAttestationResponse(
        group_id=None,  # None для режима "все группы"
        group_code="ALL",  # Специальный код для режима "Все студенты"
        attestation_type=attestation_type,
        calculated_at=datetime.now(timezone.utc),
        total_students=total_count,  # Общее количество (не пагинированное)
        passing_students=passing_students,
        failing_students=failing_students,
        grade_distribution=grade_distribution,
        average_score=round(average_score, 2),
        students=paginated_results,
        errors=errors
    )


# ============== Audit History Endpoint ==============

@router.get("/attestation/settings/audit")
async def get_settings_audit_history(
    attestation_type: Optional[AttestationTypeSchema] = Query(
        default=None, description="Фильтр по типу аттестации"
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Лимит записей"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Получить историю изменений настроек аттестации (audit trail).
    
    Args:
        attestation_type: Фильтр по типу аттестации (опционально)
        limit: Максимальное количество записей
    
    Returns:
        Список записей аудита с информацией об изменениях
    """
    audit_service = AttestationAuditService(db)
    
    logs = await audit_service.get_audit_history(
        attestation_type=attestation_type,
        limit=limit
    )
    
    return [
        {
            "id": str(log.id),
            "settings_type": log.settings_type,
            "settings_key": log.settings_key,
            "action": log.action,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "changed_fields": log.changed_fields,
            "changed_by_id": str(log.changed_by_id) if log.changed_by_id else None,
            "changed_by_name": log.changed_by.full_name if log.changed_by else None,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
