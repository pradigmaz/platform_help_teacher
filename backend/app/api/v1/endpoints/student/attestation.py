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
from app.services.attestation.subject_scope import list_group_subject_options_in_period
from app.services.attestation_service import AttestationService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/attestation/subjects/{attestation_type}", response_model=list[AttestationSubjectOption])
async def get_my_attestation_subjects(
    attestation_type: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AttestationSubjectOption]:
    """Вернуть предметы текущего студента, доступные в периоде аттестации."""
    if not current_user.group_id:
        return []

    att_type = AttestationType.SECOND if attestation_type == "second" else AttestationType.FIRST
    service = AttestationService(db)
    settings = await service.get_or_create_settings(att_type)
    subjects = await list_group_subject_options_in_period(db, current_user.group_id, settings)
    return [AttestationSubjectOption(id=subject.id, name=subject.name, code=subject.code) for subject in subjects]


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

    if attestation_type not in ("first", "second"):
        raise HTTPException(status_code=400, detail=em.INVALID_ATTESTATION_TYPE)

    if not current_user.group_id:
        return {
            "attestation_type": attestation_type,
            "error": "Студент не привязан к группе",
            "total_score": 0,
            "grade": "-",
            "is_passing": False,
        }

    try:
        att_type = AttestationType.FIRST if attestation_type == "first" else AttestationType.SECOND

        service = AttestationService(db)
        result = await service.calculate_student_score(
            student_id=current_user.id,
            group_id=current_user.group_id,
            attestation_type=att_type,
            activity_points=0,
            subject_id=subject_id,
        )

        b = result.breakdown
        return {
            "attestation_type": attestation_type,
            "subject_id": str(result.subject_id) if result.subject_id else None,
            "total_score": result.total_score,
            "grade": result.grade,
            "is_passing": result.is_passing,
            "max_points": result.max_points,
            "min_passing_points": result.min_passing_points,
            "breakdown": {
                "labs": {
                    "score": b.labs_score,
                    "max": b.labs_max,
                    "count": b.labs_count,
                    "required": b.labs_required,
                },
                "attendance": {
                    "score": b.attendance_score,
                    "max": b.attendance_max,
                    "ratio": b.attendance_ratio,
                    "total_classes": b.total_classes,
                    "present": b.present_count,
                    "late": b.late_count,
                },
                "activity": {
                    "score": b.activity_score,
                    "max": b.activity_max,
                    "bonus_blocked": b.bonus_blocked,
                },
            },
        }
    except ValueError as e:
        # Бизнес-ошибка (напр. студент не найден, некорректные данные)
        return {
            "attestation_type": attestation_type,
            "error": str(e) or "Ошибка расчёта аттестации",
            "total_score": 0,
            "grade": "-",
            "is_passing": False,
            "calculation_status": "error",
        }
    except Exception:
        # Системная ошибка — логируем и возвращаем 500
        logger.error(
            f"Attestation calc error: student={current_user.id}, type={attestation_type}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при расчёте аттестации")
