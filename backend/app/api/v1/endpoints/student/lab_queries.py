"""Shared student lab queries for endpoints and dashboard bootstrap."""

import logging
from collections import defaultdict
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.student.lab_response import format_submission, serialize_visibility_fields
from app.core import error_messages as em
from app.crud.crud_group_subject_offering import list_group_subject_ids_for_current_semester
from app.models.lab import Lab
from app.models.user import User
from app.services.lab_visibility import LabVisibilityService
from app.services.lab_visibility.models import LabVisibilityInfo
from app.services.student_lab_service import resolve_lab_acceptance, student_lab_service

logger = logging.getLogger(__name__)


async def list_student_labs(
    db: AsyncSession,
    current_user: User,
) -> list[dict[str, Any]]:
    """Build student labs list with availability and submission state."""
    if not current_user.group_id:
        return []

    visibility_service = LabVisibilityService(db)
    visible_by_subject = await visibility_service.get_visible_lab_numbers_by_subject(
        group_id=current_user.group_id,
        subgroup=current_user.subgroup,
    )
    offering_subject_ids = set(
        await list_group_subject_ids_for_current_semester(db, group_id=current_user.group_id)
    )
    if offering_subject_ids:
        visible_by_subject = {
            subject_id: work_numbers
            for subject_id, work_numbers in visible_by_subject.items()
            if subject_id in offering_subject_ids
        }
        group_subject_ids = offering_subject_ids
    else:
        group_subject_ids = await visibility_service.get_group_subject_ids(
            group_id=current_user.group_id,
            subgroup=current_user.subgroup,
        )
        if group_subject_ids:
            logger.info(
                "student_lab_subjects_fallback_to_lessons group_id=%s subject_count=%s",
                current_user.group_id,
                len(group_subject_ids),
            )

    labs = await student_lab_service.get_published_labs(db)

    def is_lab_relevant(lab: Lab) -> bool:
        if lab.subject_id:
            return lab.subject_id in visible_by_subject or lab.subject_id in group_subject_ids
        return any(lab.number in work_numbers for work_numbers in visible_by_subject.values())

    relevant_labs = [lab for lab in labs if is_lab_relevant(lab)]

    labs_by_subject: dict[UUID | None, list[Lab]] = defaultdict(list)
    for lab in relevant_labs:
        labs_by_subject[lab.subject_id].append(lab)

    visibility_by_subject: dict[UUID | None, dict[int, LabVisibilityInfo]] = {}
    for subject_id, subject_labs in labs_by_subject.items():
        visibility_by_subject[subject_id] = await visibility_service.get_batch_visibility_info(
            lab_numbers=[lab.number for lab in subject_labs],
            group_id=current_user.group_id,
            subgroup=current_user.subgroup,
            labs_deadlines={lab.number: (lab.deadline_5_lessons, lab.deadline_4_lessons) for lab in subject_labs},
            labs_subjects={lab.number: subject_id for lab in subject_labs},
            labs_ids={lab.number: lab.id for lab in subject_labs},
            student_id=current_user.id,
        )

    submissions = await student_lab_service.get_user_submissions(db, current_user.id)
    journal_grades_by_subject = await student_lab_service.get_user_journal_grades_by_subject(db, current_user.id)
    student_position = await student_lab_service.get_student_position(db, current_user)

    result: list[dict[str, Any]] = []
    prev_accepted = True

    for lab in relevant_labs:
        submission = submissions.get(lab.id)
        subject_grades = journal_grades_by_subject.get(lab.subject_id, {}) if lab.subject_id else {}
        journal_grade = subject_grades.get(lab.number)
        is_accepted, journal_grade_value, acceptance_source = resolve_lab_acceptance(submission, journal_grade)

        variant_number = None
        if lab.variants and student_position:
            variant_number = ((student_position - 1) % len(lab.variants)) + 1

        visibility_info = visibility_by_subject.get(lab.subject_id, {}).get(lab.number)
        is_available = (prev_accepted or not lab.is_sequential) and bool(visibility_info and visibility_info.is_visible)

        result.append(
            {
                "id": str(lab.id),
                "number": lab.number,
                "title": lab.title,
                "topic": lab.topic,
                "description": lab.description,
                "subject_id": str(lab.subject_id) if lab.subject_id else None,
                "deadline_5_lessons": lab.deadline_5_lessons,
                "deadline_4_lessons": lab.deadline_4_lessons,
                "max_grade": lab.max_grade,
                "current_max_grade": visibility_info.current_max_grade if visibility_info else lab.max_grade,
                "is_available": is_available,
                "is_accepted": is_accepted,
                "journal_grade": journal_grade_value,
                "acceptance_source": acceptance_source,
                "variant_number": variant_number,
                "submission": format_submission(submission) if submission else None,
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


async def get_student_lab_detail_response(
    db: AsyncSession,
    current_user: User,
    lab_id: UUID,
) -> dict[str, Any]:
    """Build lab detail payload for a student."""
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
        variant_number = ((student_position - 1) % len(lab.variants)) + 1
        for variant in lab.variants:
            if variant.get("number") == variant_number:
                variant_data = variant
                break

    submission = await student_lab_service.get_user_submission_for_lab(db, current_user.id, lab_id)
    journal_grades_by_subject = await student_lab_service.get_user_journal_grades_by_subject(db, current_user.id)
    subject_grades = journal_grades_by_subject.get(lab.subject_id, {}) if lab.subject_id else {}
    journal_grade = subject_grades.get(lab.number)
    is_accepted, journal_grade_value, acceptance_source = resolve_lab_acceptance(submission, journal_grade)

    response = {
        "id": str(lab.id),
        "number": lab.number,
        "title": lab.title,
        "topic": lab.topic,
        "subject_id": str(lab.subject_id) if lab.subject_id else None,
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
        "submission": format_submission(submission) if submission else None,
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
