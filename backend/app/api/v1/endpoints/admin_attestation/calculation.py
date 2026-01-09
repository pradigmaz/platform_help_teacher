"""Attestation calculation endpoints."""
from typing import Dict
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.core.limiter import limiter
from app.models import User, Group, UserRole
from app.services.attestation_service import AttestationService
from app.schemas.attestation import (
    AttestationResultResponse,
    GroupAttestationResponse,
    AttestationType as AttestationTypeSchema,
)

router = APIRouter()


@router.get("/attestation/calculate/{student_id}/{attestation_type}", response_model=AttestationResultResponse)
@limiter.limit("30/minute")
async def calculate_student_attestation(
    request: Request,
    student_id: UUID,
    attestation_type: AttestationTypeSchema,
    activity_points: float = Query(default=0.0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Рассчитать баллы аттестации для студента."""
    student_result = await db.execute(select(User).where(User.id == student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    if not student.group_id:
        raise HTTPException(status_code=400, detail="Студент не состоит в группе")
    
    service = AttestationService(db)
    
    try:
        result = await service.calculate_student_score(
            student_id=student_id,
            group_id=student.group_id,
            attestation_type=attestation_type,
            activity_points=activity_points
        )
        return AttestationResultResponse(**result.model_dump())
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
    """Рассчитать баллы аттестации для группы."""
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    students_result = await db.execute(
        select(User).where(
            User.group_id == group_id,
            User.role == UserRole.STUDENT,
            User.is_active == True
        )
    )
    students = list(students_result.scalars().all())
    
    if not students:
        raise HTTPException(status_code=404, detail="В группе нет активных студентов")
    
    service = AttestationService(db)
    results, errors = await service.calculate_group_scores_batch(
        group_id=group_id,
        attestation_type=attestation_type,
        students=students
    )
    
    return _build_group_response(group_id, group.code, attestation_type, results, errors)


def _build_group_response(group_id, group_code, attestation_type, results, errors):
    """Построить ответ для группы."""
    passing = sum(1 for r in results if r.is_passing)
    
    grade_dist: Dict[str, int] = {"неуд": 0, "уд": 0, "хор": 0, "отл": 0}
    for r in results:
        if r.grade in grade_dist:
            grade_dist[r.grade] += 1
    
    avg = sum(r.total_score for r in results) / len(results) if results else 0.0
    
    return GroupAttestationResponse(
        group_id=group_id,
        group_code=group_code,
        attestation_type=attestation_type,
        calculated_at=datetime.now(timezone.utc),
        total_students=len(results),
        passing_students=passing,
        failing_students=len(results) - passing,
        grade_distribution=grade_dist,
        average_score=round(avg, 2),
        students=results,
        errors=errors
    )
