"""Student dashboard bootstrap endpoint."""

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.endpoints.public_semester import load_public_semester_info
from app.api.v1.endpoints.student.attendance import build_attendance_stats, list_student_attendance_records
from app.api.v1.endpoints.student.attestation import (
    calculate_student_attestation_response,
    list_student_attestation_subjects,
)
from app.api.v1.endpoints.student.lab_queries import list_student_labs
from app.api.v1.endpoints.student.notifications import list_student_announcements
from app.api.v1.endpoints.student.profile import build_student_profile
from app.audit import ActionType, EntityType, audit_action
from app.models.user import User
from app.schemas.student_dashboard import StudentDashboardBootstrapResponse
from app.services.schedule_constants import today_msk

router = APIRouter()


def resolve_preferred_attestation_type(
    semester_start_date: str | None,
    academic_year: int,
    semester: int,
) -> str:
    """Mirror frontend preferred attestation type logic."""
    if semester_start_date:
        semester_start = datetime.fromisoformat(semester_start_date).date()
    elif semester == 1:
        semester_start = datetime(academic_year, 9, 1).date()
    else:
        semester_start = datetime(academic_year + 1, 1, 1).date()

    second_start = semester_start + timedelta(weeks=8)
    return "first" if today_msk() < second_start else "second"


async def resolve_current_attestation(
    db: AsyncSession,
    current_user: User,
    preferred_type: str,
    labs: list[dict],
) -> dict | None:
    """Resolve the attestation that should be shown on the dashboard."""
    lab_subject_ids = {
        UUID(subject_id)
        for subject_id in (lab.get("subject_id") for lab in labs)
        if isinstance(subject_id, str) and subject_id
    }
    resolved_subject_id = next(iter(lab_subject_ids), None) if len(lab_subject_ids) == 1 else None

    if resolved_subject_id is None:
        subjects = await list_student_attestation_subjects(db, current_user, preferred_type)
        if len(subjects) == 1:
            resolved_subject_id = subjects[0].id
        elif len(subjects) > 1:
            return {
                "attestation_type": preferred_type,
                "subject_id": None,
                "total_score": 0,
                "grade": "-",
                "is_passing": False,
                "error": "Для расчёта аттестации нужно выбрать предмет",
            }

    preferred = await calculate_student_attestation_response(
        db,
        current_user,
        preferred_type,
        subject_id=resolved_subject_id,
    )
    if not preferred.get("error"):
        return preferred

    fallback_type = "second" if preferred_type == "first" else "first"
    return await calculate_student_attestation_response(
        db,
        current_user,
        fallback_type,
        subject_id=resolved_subject_id,
    )


@router.get("/dashboard/bootstrap", response_model=StudentDashboardBootstrapResponse)
@audit_action(ActionType.VIEW, EntityType.PROFILE)
async def get_dashboard_bootstrap(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentDashboardBootstrapResponse:
    """Aggregate payload for the student dashboard home screen."""
    profile = await build_student_profile(db, current_user)
    semester = await load_public_semester_info(db)
    announcements = await list_student_announcements(db, current_user, skip=0, limit=10)
    labs = await list_student_labs(db, current_user)
    attendance_records = await list_student_attendance_records(db, current_user)
    preferred_type = resolve_preferred_attestation_type(
        semester.get("semester_start_date"),
        int(semester["academic_year"]),
        int(semester["semester"]),
    )
    current_attestation = await resolve_current_attestation(db, current_user, preferred_type, labs)

    return StudentDashboardBootstrapResponse.model_validate(
        {
            "profile": profile,
            "semester": semester,
            "announcements": [announcement.model_dump(mode="json") for announcement in announcements],
            "overview": {
                "attendance_stats": build_attendance_stats(attendance_records),
                "labs": labs,
                "attestation_type": preferred_type,
                "current_attestation": current_attestation,
            },
        }
    )
