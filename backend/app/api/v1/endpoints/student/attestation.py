"""Student attestation endpoint."""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.audit import ActionType, EntityType, audit_action
from app.core import error_messages as em
from app.models.attestation_settings import AttestationType
from app.models.user import User
from app.schemas.attestation import AttestationSubjectOption
from app.services.attestation.automatic_queue import resolve_student_automatic_offering
from app.services.attestation.student_automatic_progress import resolve_student_automatic_progress
from app.services.attestation.student_lab_progress_plan import build_student_lab_progress_plan
from app.services.attestation.subject_scope import list_group_subject_options_in_period
from app.services.attestation_service import AttestationService
from app.services.offering_policy_resolver import resolve_offering_policy

router = APIRouter()
logger = logging.getLogger(__name__)


def resolve_student_attestation_type(attestation_type: str) -> AttestationType:
    """Resolve public attestation type string to enum."""
    if attestation_type not in ("first", "second"):
        raise HTTPException(status_code=400, detail=em.INVALID_ATTESTATION_TYPE)
    return AttestationType.FIRST if attestation_type == "first" else AttestationType.SECOND


async def list_student_attestation_subjects(
    db: AsyncSession,
    current_user: User,
    attestation_type: str,
) -> list[AttestationSubjectOption]:
    """Return subject options for the student's attestation period."""
    if not current_user.group_id:
        return []

    att_type = resolve_student_attestation_type(attestation_type)
    service = AttestationService(db)
    settings = await service.get_or_create_settings(att_type)
    subjects = await list_group_subject_options_in_period(db, current_user.group_id, settings)
    return [AttestationSubjectOption(id=subject.id, name=subject.name, code=subject.code) for subject in subjects]


async def resolve_student_lab_progress_plan(
    db: AsyncSession,
    current_user: User,
    *,
    subject_id: UUID | None = None,
) -> dict[str, int | str | bool | None] | None:
    """Resolve the shared lab thresholds that should be visible to a student."""
    offering_resolution = await resolve_student_automatic_offering(
        db,
        student=current_user,
        subject_id=subject_id,
    )
    if offering_resolution.offering is None and offering_resolution.reason in {"subject_required", "offering_missing"}:
        return None

    policy = await resolve_offering_policy(db, offering_resolution.offering)
    automatic_progress = await resolve_student_automatic_progress(
        db,
        student=current_user,
        subject_id=subject_id,
        total_labs=policy.automatic_required_labs_total,
        automatic_places=policy.automatic_places,
        automatic_enabled=policy.automatic_enabled,
        offering=offering_resolution.offering,
    )
    effective_automatic_enabled = policy.automatic_enabled and automatic_progress.automatic_reason in {None, "refused"}

    return build_student_lab_progress_plan(
        total_labs=policy.total_labs,
        first_required=policy.labs_required_first,
        second_required=policy.labs_required_second_extra,
        second_total_required=policy.labs_required_second_total,
        exam_admission_required_labs=policy.exam_admission_required_labs,
        automatic_required_labs_total=policy.automatic_required_labs_total,
        automatic_enabled=effective_automatic_enabled,
        automatic_places=policy.automatic_places,
        completed_count=automatic_progress.completed_count,
        automatic_remaining=automatic_progress.automatic_remaining,
        automatic_queue_position=automatic_progress.queue_position,
        automatic_is_winner=automatic_progress.is_winner,
        automatic_completion_at=automatic_progress.completion_at,
        automatic_reason=automatic_progress.automatic_reason,
        automatic_declined=automatic_progress.automatic_declined,
    )


async def calculate_student_attestation_response(
    db: AsyncSession,
    current_user: User,
    attestation_type: str,
    *,
    subject_id: UUID | None = None,
) -> dict[str, Any]:
    """Calculate attestation payload for a student."""
    if not current_user.group_id:
        lab_progress_plan = await resolve_student_lab_progress_plan(db, current_user, subject_id=subject_id)
        return {
            "attestation_type": attestation_type,
            "error": "Студент не привязан к группе",
            "total_score": 0,
            "grade": "-",
            "is_passing": False,
            "lab_progress_plan": lab_progress_plan,
        }

    lab_progress_plan = await resolve_student_lab_progress_plan(db, current_user, subject_id=subject_id)

    try:
        service = AttestationService(db)
        result = await service.calculate_student_score(
            student_id=current_user.id,
            group_id=current_user.group_id,
            attestation_type=resolve_student_attestation_type(attestation_type),
            activity_points=0,
            subject_id=subject_id,
        )

        breakdown = result.breakdown
        return {
            "attestation_type": attestation_type,
            "subject_id": str(result.subject_id) if result.subject_id else None,
            "total_score": result.total_score,
            "grade": result.grade,
            "is_passing": result.is_passing,
            "max_points": result.max_points,
            "min_passing_points": result.min_passing_points,
            "lab_progress_plan": lab_progress_plan,
            "breakdown": {
                "labs": {
                    "score": breakdown.labs_score,
                    "max": breakdown.labs_max,
                    "count": breakdown.labs_count,
                    "required": breakdown.labs_required,
                },
                "attendance": {
                    "score": breakdown.attendance_score,
                    "max": breakdown.attendance_max,
                    "ratio": breakdown.attendance_ratio,
                    "total_classes": breakdown.total_classes,
                    "present": breakdown.present_count,
                    "late": breakdown.late_count,
                },
                "activity": {
                    "score": breakdown.activity_score,
                    "max": breakdown.activity_max,
                    "bonus_blocked": breakdown.bonus_blocked,
                },
            },
        }
    except ValueError as error:
        return {
            "attestation_type": attestation_type,
            "error": str(error) or "Ошибка расчёта аттестации",
            "total_score": 0,
            "grade": "-",
            "is_passing": False,
            "calculation_status": "error",
            "lab_progress_plan": lab_progress_plan,
        }
    except Exception:
        logger.error(
            f"Attestation calc error: student={current_user.id}, type={attestation_type}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при расчёте аттестации")


@router.get("/attestation/subjects/{attestation_type}", response_model=list[AttestationSubjectOption])
async def get_my_attestation_subjects(
    attestation_type: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AttestationSubjectOption]:
    """Вернуть предметы текущего студента, доступные в периоде аттестации."""
    return await list_student_attestation_subjects(db, current_user, attestation_type)


@router.get("/attestation/{attestation_type}")
@audit_action(ActionType.VIEW, EntityType.ATTESTATION)
async def get_my_attestation(
    attestation_type: str,
    request: Request,
    subject_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Баллы аттестации студента."""
    return await calculate_student_attestation_response(
        db,
        current_user,
        attestation_type,
        subject_id=subject_id,
    )
