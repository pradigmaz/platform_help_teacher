"""Student labs endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.audit import ActionType, EntityType, audit_action, audit_user
from app.core import error_messages as em
from app.core.limiter import limiter
from app.models.lab import Lab
from app.models.submission import Submission
from app.models.user import User
from app.services.lab_visibility import LabVisibilityService
from app.services.student_lab_service import student_lab_service

router = APIRouter()


def _format_submission(sub: Submission) -> dict:
    return {
        "id": str(sub.id),
        "status": sub.status.value,
        "grade": sub.grade,
        "feedback": sub.feedback,
        "ready_at": sub.ready_at.isoformat() if sub.ready_at else None,
        "accepted_at": sub.accepted_at.isoformat() if sub.accepted_at else None,
    }


@router.get("/labs")
@audit_action(ActionType.VIEW, EntityType.LAB)
async def get_my_labs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Лабораторные работы студента со статусами сдачи."""
    if not current_user.group_id:
        return []

    visibility_service = LabVisibilityService(db)
    visible_by_subject = await visibility_service.get_visible_lab_numbers_by_subject(
        group_id=current_user.group_id, subgroup=current_user.subgroup
    )

    labs = await student_lab_service.get_published_labs(db)

    def is_lab_visible(lab: Lab) -> bool:
        if lab.subject_id:
            return lab.number in visible_by_subject.get(lab.subject_id, [])
        return any(lab.number in work_numbers for work_numbers in visible_by_subject.values())

    visible_labs = [lab for lab in labs if is_lab_visible(lab)]

    # Batch-загрузка дедлайнов
    labs_deadlines = {l.number: (l.deadline_5_lessons, l.deadline_4_lessons) for l in visible_labs}
    labs_subjects = {l.number: l.subject_id for l in visible_labs}
    labs_ids = {l.number: l.id for l in visible_labs}
    visibility_map = await visibility_service.get_batch_visibility_info(
        lab_numbers=[l.number for l in visible_labs],
        group_id=current_user.group_id,
        subgroup=current_user.subgroup,
        labs_deadlines=labs_deadlines,
        labs_subjects=labs_subjects,
        labs_ids=labs_ids,
    )

    submissions = await student_lab_service.get_user_submissions(db, current_user.id)
    journal_grades = await student_lab_service.get_user_journal_grades(db, current_user.id)
    student_position = await student_lab_service.get_student_position(db, current_user)

    result = []
    prev_accepted = True

    for lab in visible_labs:
        sub = submissions.get(lab.id)
        journal_grade = journal_grades.get(lab.number)
        is_available = prev_accepted or not lab.is_sequential

        variant_number = None
        if lab.variants and student_position:
            variant_number = ((student_position - 1) % len(lab.variants)) + 1

        visibility_info = visibility_map.get(lab.number)

        submission_data = None
        if sub:
            submission_data = _format_submission(sub)
        elif journal_grade:
            submission_data = {
                "id": str(journal_grade.id),
                "status": "ACCEPTED",
                "grade": journal_grade.grade,
                "feedback": None,
                "ready_at": None,
                "accepted_at": journal_grade.created_at.isoformat() if journal_grade.created_at else None,
            }

        result.append(
            {
                "id": str(lab.id),
                "number": lab.number,
                "title": lab.title,
                "topic": lab.topic,
                "description": lab.description,
                "deadline_5_lessons": lab.deadline_5_lessons,
                "deadline_4_lessons": lab.deadline_4_lessons,
                "max_grade": lab.max_grade,
                "current_max_grade": visibility_info.current_max_grade if visibility_info else lab.max_grade,
                "is_available": is_available,
                "variant_number": variant_number,
                "submission": submission_data,
                "visible_from": visibility_info.visible_from.isoformat()
                if visibility_info and visibility_info.visible_from
                else None,
                "deadline_active_from": visibility_info.deadline_active_from.isoformat()
                if visibility_info and visibility_info.deadline_active_from
                else None,
                "deadline_5_status": visibility_info.deadline_5_status if visibility_info else None,
                "deadline_4_status": visibility_info.deadline_4_status if visibility_info else None,
                "lessons_until_deadline_5": visibility_info.lessons_until_deadline_5 if visibility_info else None,
                "lessons_until_deadline_4": visibility_info.lessons_until_deadline_4 if visibility_info else None,
                "has_extension": visibility_info.has_extension if visibility_info else False,
                "extension_bonus": visibility_info.extension_bonus if visibility_info else 0,
            }
        )

        is_accepted = (sub and sub.status.value == "ACCEPTED") or journal_grade is not None
        if is_accepted:
            prev_accepted = True
        elif lab.is_sequential:
            prev_accepted = False

    return result


@router.get("/labs/{lab_id}")
@audit_action(ActionType.VIEW, EntityType.LAB_DETAIL, "lab_id")
async def get_lab_detail(
    lab_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Детали лабораторной работы с вариантом студента."""
    lab = await student_lab_service.get_lab_by_id(db, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail=em.LAB_NOT_FOUND)

    visibility_info = None
    visibility_service = None
    if current_user.group_id:
        visibility_service = LabVisibilityService(db)
        visibility_info = await visibility_service.get_visibility_info(
            lab_number=lab.number,
            group_id=current_user.group_id,
            subgroup=current_user.subgroup,
            deadline_5_lessons=lab.deadline_5_lessons,
            deadline_4_lessons=lab.deadline_4_lessons,
            subject_id=lab.subject_id,
        )
        if not visibility_info.is_visible:
            raise HTTPException(status_code=403, detail=em.LAB_NOT_AVAILABLE_YET)

    is_available = await student_lab_service.check_lab_availability(db, current_user.id, lab)
    student_position = await student_lab_service.get_student_position(db, current_user)

    variant_number = None
    variant_data = None
    if lab.variants and student_position:
        variants_count = len(lab.variants)
        variant_number = ((student_position - 1) % variants_count) + 1
        for v in lab.variants:
            if v.get("number") == variant_number:
                variant_data = v
                break

    sub = await student_lab_service.get_user_submission_for_lab(db, current_user.id, lab_id)

    response = {
        "id": str(lab.id),
        "number": lab.number,
        "title": lab.title,
        "topic": lab.topic,
        "goal": lab.goal,
        "formatting_guide": lab.formatting_guide,
        "theory_content": lab.theory_content,
        "practice_content": lab.practice_content,
        "questions": lab.questions,
        "deadline_5_lessons": lab.deadline_5_lessons,
        "deadline_4_lessons": lab.deadline_4_lessons,
        "max_grade": lab.max_grade,
        "is_available": is_available,
        "variant_number": variant_number,
        "variant_data": variant_data,
        "submission": _format_submission(sub) if sub else None,
    }

    if visibility_info:
        response.update(
            {
                "visible_from": visibility_info.visible_from.isoformat() if visibility_info.visible_from else None,
                "deadline_active_from": visibility_info.deadline_active_from.isoformat()
                if visibility_info.deadline_active_from
                else None,
                "deadline_5_status": visibility_info.deadline_5_status,
                "deadline_4_status": visibility_info.deadline_4_status,
                "lessons_until_deadline_5": visibility_info.lessons_until_deadline_5,
                "lessons_until_deadline_4": visibility_info.lessons_until_deadline_4,
            }
        )

    can_submit_now = False
    if current_user.group_id and visibility_service:
        can_submit_now = await visibility_service.is_lab_session_now(
            group_id=current_user.group_id,
            subgroup=current_user.subgroup,
            subject_id=lab.subject_id,
        )
    response["can_submit_now"] = can_submit_now

    return response


@router.post("/labs/{lab_id}/ready")
@limiter.limit("10/hour")
@audit_action(ActionType.SUBMIT, EntityType.SUBMISSION, "lab_id")
async def mark_lab_ready(
    lab_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(audit_user),
) -> dict[str, Any]:
    """Отметить лабу как готовую к сдаче. Rate limit: 10/hour."""
    lab = await student_lab_service.get_lab_by_id(db, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail=em.LAB_NOT_FOUND)

    if current_user.group_id:
        visibility_service = LabVisibilityService(db)
        visibility_info = await visibility_service.get_visibility_info(
            lab_number=lab.number,
            group_id=current_user.group_id,
            subgroup=current_user.subgroup,
            deadline_5_lessons=lab.deadline_5_lessons,
            deadline_4_lessons=lab.deadline_4_lessons,
            subject_id=lab.subject_id,
        )
        if not visibility_info.is_visible:
            raise HTTPException(status_code=403, detail=em.LAB_NOT_AVAILABLE_BY_SCHEDULE)

        is_session_now = await visibility_service.is_lab_session_now(
            group_id=current_user.group_id,
            subgroup=current_user.subgroup,
            subject_id=lab.subject_id,
        )
        if not is_session_now:
            raise HTTPException(status_code=403, detail="Сдача доступна только во время пары")

    is_available = await student_lab_service.check_lab_availability(db, current_user.id, lab)
    if not is_available:
        raise HTTPException(status_code=403, detail=em.LAB_NOT_AVAILABLE_YET)

    student_position = await student_lab_service.get_student_position(db, current_user)
    variant_number = None
    if lab.variants and student_position:
        variant_number = ((student_position - 1) % len(lab.variants)) + 1

    try:
        sub = await student_lab_service.mark_ready(db, current_user.id, lab_id, variant_number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "ready",
        "submission_id": str(sub.id),
        "variant_number": variant_number,
        "message": "You are now in the queue.",
    }


@router.post("/labs/{lab_id}/cancel-ready")
@audit_action(ActionType.CANCEL, EntityType.SUBMISSION, "lab_id")
async def cancel_lab_ready(
    lab_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(audit_user),
) -> dict[str, Any]:
    """Отменить готовность к сдаче."""
    try:
        await student_lab_service.cancel_ready(db, current_user.id, lab_id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    return {"status": "cancelled", "message": "Removed from queue"}
