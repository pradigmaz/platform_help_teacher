"""Student labs response serializers."""

from dataclasses import asdict

from app.models.submission import Submission
from app.services.deadline_trace import build_deadline_trace_from_visibility_info
from app.services.lab_visibility.models import LabVisibilityInfo


def format_submission(sub: Submission) -> dict:
    """Serialize submission payload shared by student lab endpoints."""
    return {
        "id": str(sub.id),
        "status": sub.status.value,
        "grade": sub.grade,
        "feedback": sub.feedback,
        "ready_at": sub.ready_at.isoformat() if sub.ready_at else None,
        "accepted_at": sub.accepted_at.isoformat() if sub.accepted_at else None,
    }


def serialize_deadline_trace(
    *,
    visibility_info: LabVisibilityInfo | None,
    deadline_5_lessons: int | None,
    deadline_4_lessons: int | None,
) -> dict | None:
    """Serialize shared deadline trace from student visibility info."""
    if visibility_info is None:
        return None
    return asdict(
        build_deadline_trace_from_visibility_info(
            visibility_info=visibility_info,
            deadline_5_lessons=deadline_5_lessons,
            deadline_4_lessons=deadline_4_lessons,
        )
    )


def serialize_visibility_fields(
    *,
    visibility_info: LabVisibilityInfo | None,
    deadline_5_lessons: int | None,
    deadline_4_lessons: int | None,
) -> dict:
    """Serialize optional visibility/deadline fields for student API responses."""
    if visibility_info is None:
        return {
            "visible_from": None,
            "deadline_active_from": None,
            "deadline_5_status": None,
            "deadline_4_status": None,
            "lessons_until_deadline_5": None,
            "lessons_until_deadline_4": None,
            "current_max_grade": 5,
            "has_extension": False,
            "extension_bonus": 0,
            "is_excused_origin": False,
            "deadline_trace": None,
        }

    return {
        "visible_from": visibility_info.visible_from.isoformat() if visibility_info.visible_from else None,
        "deadline_active_from": visibility_info.deadline_active_from.isoformat()
        if visibility_info.deadline_active_from
        else None,
        "deadline_5_status": visibility_info.deadline_5_status,
        "deadline_4_status": visibility_info.deadline_4_status,
        "lessons_until_deadline_5": visibility_info.lessons_until_deadline_5,
        "lessons_until_deadline_4": visibility_info.lessons_until_deadline_4,
        "current_max_grade": visibility_info.current_max_grade,
        "has_extension": visibility_info.has_extension,
        "extension_bonus": visibility_info.extension_bonus,
        "is_excused_origin": visibility_info.is_excused_origin,
        "deadline_trace": serialize_deadline_trace(
            visibility_info=visibility_info,
            deadline_5_lessons=deadline_5_lessons,
            deadline_4_lessons=deadline_4_lessons,
        ),
    }
