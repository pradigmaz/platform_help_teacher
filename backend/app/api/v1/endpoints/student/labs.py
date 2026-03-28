"""Student labs endpoints."""

from collections import defaultdict
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.endpoints.student.lab_response import format_submission, serialize_visibility_fields
from app.audit import ActionType, EntityType, audit_action
from app.audit.deps import audit_user
from app.core import error_messages as em
from app.core.limiter import limiter
from app.models.lab import Lab
from app.models.user import User
from app.services.lab_visibility import LabVisibilityService
from app.services.lab_visibility.models import LabVisibilityInfo
from app.services.student_lab_service import resolve_lab_acceptance, student_lab_service

router = APIRouter()


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
    group_subject_ids = await visibility_service.get_group_subject_ids(
        group_id=current_user.group_id, subgroup=current_user.subgroup
    )

    labs = await student_lab_service.get_published_labs(db)

    def is_lab_relevant(lab: Lab) -> bool:
        if lab.subject_id:
            return lab.subject_id in visible_by_subject or lab.subject_id in group_subject_ids
        return any(lab.number in work_numbers for work_numbers in visible_by_subject.values())

    relevant_labs = [lab for lab in labs if is_lab_relevant(lab)]

    # Batch-загрузка дедлайнов
    labs_by_subject: dict[UUID | None, list[Lab]] = defaultdict(list)
    for lab in relevant_labs:
        labs_by_subject[lab.subject_id].append(lab)

    visibility_by_subject: dict[UUID | None, dict[int, LabVisibilityInfo]] = {}
    for subject_id, subject_labs in labs_by_subject.items():
        subject_visibility = await visibility_service.get_batch_visibility_info(
            lab_numbers=[lab.number for lab in subject_labs],
            group_id=current_user.group_id,
            subgroup=current_user.subgroup,
            labs_deadlines={lab.number: (lab.deadline_5_lessons, lab.deadline_4_lessons) for lab in subject_labs},
            labs_subjects={lab.number: subject_id for lab in subject_labs},
            labs_ids={lab.number: lab.id for lab in subject_labs},
            student_id=current_user.id,
        )
        visibility_by_subject[subject_id] = subject_visibility

    submissions = await student_lab_service.get_user_submissions(db, current_user.id)
    journal_grades_by_subject = await student_lab_service.get_user_journal_grades_by_subject(db, current_user.id)
    student_position = await student_lab_service.get_student_position(db, current_user)

    result = []
    prev_accepted = True

    for lab in relevant_labs:
        sub = submissions.get(lab.id)
        # BUG-7 fix: фильтруем оценки по subject_id лабы
        subject_grades = journal_grades_by_subject.get(lab.subject_id, {}) if lab.subject_id else {}
        journal_grade = subject_grades.get(lab.number)
        is_accepted, journal_grade_value, acceptance_source = resolve_lab_acceptance(sub, journal_grade)

        variant_number = None
        if lab.variants and student_position:
            variant_number = ((student_position - 1) % len(lab.variants)) + 1

        visibility_info = visibility_by_subject.get(lab.subject_id, {}).get(lab.number)
        is_available = (prev_accepted or not lab.is_sequential) and bool(visibility_info and visibility_info.is_visible)

        submission_data = None
        if sub:
            submission_data = format_submission(sub)
            # [StudentLabs:get_my_labs] Found submission for lab {lab.number}

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
                "is_accepted": is_accepted,
                "journal_grade": journal_grade_value,
                "acceptance_source": acceptance_source,
                "variant_number": variant_number,
                "submission": submission_data,
                **serialize_visibility_fields(
                    visibility_info=visibility_info,
                    deadline_5_lessons=lab.deadline_5_lessons,
                    deadline_4_lessons=lab.deadline_4_lessons,
                ),
            }
        )

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
            lab_id=lab.id,
            student_id=current_user.id,
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
    journal_grades_by_subject = await student_lab_service.get_user_journal_grades_by_subject(db, current_user.id)
    subject_grades = journal_grades_by_subject.get(lab.subject_id, {}) if lab.subject_id else {}
    journal_grade = subject_grades.get(lab.number)
    is_accepted, journal_grade_value, acceptance_source = resolve_lab_acceptance(sub, journal_grade)

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
        "is_accepted": is_accepted,
        "journal_grade": journal_grade_value,
        "acceptance_source": acceptance_source,
        "variant_number": variant_number,
        "variant_data": variant_data,
        "submission": format_submission(sub) if sub else None,
    }

    if visibility_info:
        response.update(
            serialize_visibility_fields(
                visibility_info=visibility_info,
                deadline_5_lessons=lab.deadline_5_lessons,
                deadline_4_lessons=lab.deadline_4_lessons,
            )
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
            lab_id=lab.id,
            student_id=current_user.id,
        )
        if not visibility_info.is_visible:
            raise HTTPException(status_code=403, detail=em.LAB_NOT_AVAILABLE_BY_SCHEDULE)

        current_lesson = await visibility_service.get_current_lab_session(
            group_id=current_user.group_id,
            subgroup=current_user.subgroup,
            subject_id=lab.subject_id,
        )
        if not current_lesson:
            raise HTTPException(status_code=403, detail="Сдача доступна только во время пары")
    else:
        current_lesson = None

    is_available = await student_lab_service.check_lab_availability(db, current_user.id, lab)
    if not is_available:
        raise HTTPException(status_code=403, detail=em.LAB_NOT_AVAILABLE_YET)

    student_position = await student_lab_service.get_student_position(db, current_user)
    variant_number = None
    if lab.variants and student_position:
        variant_number = ((student_position - 1) % len(lab.variants)) + 1

    try:
        sub = await student_lab_service.mark_ready(
            db,
            current_user.id,
            lab_id,
            variant_number,
            lesson=current_lesson,
        )
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
