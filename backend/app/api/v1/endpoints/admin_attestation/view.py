"""Aggregate admin attestation view endpoint."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.db.session import get_db
from app.models import Group, Subject, User, UserRole
from app.schemas.attestation import (
    AttestationSubjectOption,
    AttestationType as AttestationTypeSchema,
    AttestationViewResponse,
)
from app.schemas.group import GroupResponse
from app.services.attestation.subject_scope import list_group_subject_options_in_period
from app.services.attestation_service import AttestationService

router = APIRouter()


@router.get("/attestation/view", response_model=AttestationViewResponse)
async def get_attestation_view(
    view_mode: str = Query(..., pattern="^(by-group|all-students)$"),
    attestation_type: AttestationTypeSchema = Query(...),
    group_id: UUID | None = Query(default=None),
    subject_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> AttestationViewResponse:
    groups_result = await db.execute(
        select(Group, func.count(User.id).label("students_count"))
        .outerjoin(User, User.group_id == Group.id)
        .where(Group.is_archived.is_(False))
        .group_by(Group.id)
        .order_by(Group.name.asc())
    )
    groups: list[GroupResponse] = []
    for group, students_count in groups_result:
        payload = GroupResponse.model_validate(group)
        payload.students_count = students_count
        groups.append(payload)

    resolved_group_id = group_id
    if view_mode == "by-group" and resolved_group_id is None and groups:
        resolved_group_id = groups[0].id

    available_subjects: list[AttestationSubjectOption] = []
    service = AttestationService(db)
    if view_mode == "all-students":
        subjects_result = await db.execute(select(Subject).where(Subject.is_active).order_by(Subject.name.asc()))
        available_subjects = [
            AttestationSubjectOption(id=subject.id, name=subject.name, code=subject.code)
            for subject in subjects_result.scalars().all()
        ]
    elif resolved_group_id is not None:
        settings = await service.get_or_create_settings(attestation_type)
        available_subjects = [
            AttestationSubjectOption(id=subject.id, name=subject.name, code=subject.code)
            for subject in await list_group_subject_options_in_period(db, resolved_group_id, settings)
        ]

    data = None
    if view_mode == "all-students":
        if subject_id is not None:
            data = await _calculate_all_students(db, service, attestation_type, subject_id)
    elif resolved_group_id is not None:
        requires_subject = len(available_subjects) > 1
        effective_subject_id = subject_id
        if len(available_subjects) == 1 and subject_id is None:
            effective_subject_id = available_subjects[0].id
        if not requires_subject or effective_subject_id is not None:
            data = await _calculate_group(db, service, resolved_group_id, attestation_type, effective_subject_id)

    return AttestationViewResponse(
        resolved_group_id=resolved_group_id,
        groups=groups,
        available_subjects=available_subjects,
        data=data,
    )


async def _calculate_group(
    db: AsyncSession,
    service: AttestationService,
    group_id: UUID,
    attestation_type: AttestationTypeSchema,
    subject_id: UUID | None,
):
    from .calculation import _build_group_response

    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    if group is None:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    students_result = await db.execute(
        select(User).where(User.group_id == group_id, User.role == UserRole.STUDENT, User.is_active)
    )
    students = list(students_result.scalars().all())
    if not students:
        return None

    results, errors = await service.calculate_group_scores_batch(
        group_id=group_id,
        attestation_type=attestation_type,
        students=students,
        subject_id=subject_id,
    )
    return _build_group_response(group_id, group.code, attestation_type, results, errors)


async def _calculate_all_students(
    db: AsyncSession,
    service: AttestationService,
    attestation_type: AttestationTypeSchema,
    subject_id: UUID,
):
    from .calculation import _build_all_students_response

    groups_result = await db.execute(
        select(Group).options(selectinload(Group.users)).where(Group.is_archived.is_(False))
    )
    groups = list(groups_result.scalars().all())
    all_results = []
    all_errors = []

    for group in groups:
        students = [user for user in group.users if user.role == UserRole.STUDENT and user.is_active]
        if not students:
            continue
        try:
            results, errors = await service.calculate_group_scores_batch(
                group_id=group.id,
                attestation_type=attestation_type,
                students=students,
                subject_id=subject_id,
            )
        except ValueError as exc:
            if "Предмет не найден" in str(exc):
                continue
            raise
        all_results.extend(results)
        all_errors.extend(errors)

    if not all_results:
        return None
    return _build_all_students_response(attestation_type, all_results, all_errors)
