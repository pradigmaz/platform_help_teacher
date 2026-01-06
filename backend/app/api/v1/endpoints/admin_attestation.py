from typing import Any, List, Dict
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.core.limiter import limiter
from app.models import User, Group, AttestationSettings, AttestationType
from app.services.attestation_service import AttestationService
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
    
    try:
        settings = await service.update_settings(settings_in)
        return service.to_response(settings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Attestation Calculation Endpoints ==============
# Requirements: 6.1, 6.2, 6.3

@router.get("/attestation/calculate/{student_id}/{attestation_type}", response_model=AttestationResultResponse)
async def calculate_student_attestation(
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
            calculated_at=datetime.utcnow()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/attestation/calculate/group/{group_id}/{attestation_type}", response_model=GroupAttestationResponse)
async def calculate_group_attestation(
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
        calculated_at=datetime.utcnow(),
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
async def calculate_all_students_attestation(
    attestation_type: AttestationTypeSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Рассчитать баллы аттестации для ВСЕХ студентов (все группы).
    
    Requirements: 1.1 - страница баллов аттестации
    Requirements: 1.2 - отображение ФИО, баллов, оценки
    
    Студенты сортируются по ФИО (А-Я).
    Каждый студент содержит group_code для отображения группы.
    
    Args:
        attestation_type: Тип аттестации (first/second)
    
    Returns:
        GroupAttestationResponse со всеми студентами и статистикой
    """
    service = AttestationService(db)
    model_type = attestation_type
    
    # Рассчитываем баллы для всех студентов
    results, errors = await service.calculate_all_students_scores(
        attestation_type=model_type
    )
    
    if not results:
        raise HTTPException(status_code=404, detail="Нет активных студентов")
    
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
        group_id=UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder для "все группы"
        group_code="ALL",  # Специальный код для режима "Все студенты"
        attestation_type=attestation_type,
        calculated_at=datetime.utcnow(),
        total_students=len(results),
        passing_students=passing_students,
        failing_students=failing_students,
        grade_distribution=grade_distribution,
        average_score=round(average_score, 2),
        students=results,
        errors=errors
    )

