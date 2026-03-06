"""
Bulk операции с оценками (оптимизированные batch-запросы).
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_teacher, get_db
from app.core import error_messages as em
from app.core.limiter import limiter
from app.models import Lesson, User
from app.models.schedule import LessonType
from app.schemas.lesson_grade import BulkGradeCreate
from app.services.attestation.deadline_validator import validate_grade_for_max
from app.services.submission_journal_sync import journal_sync

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/grades/bulk")
@limiter.limit("30/minute")
async def bulk_update_grades(
    request: Request,
    data: BulkGradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Массовое создание/обновление оценок с проверкой дедлайна и слотов."""
    lesson_result = await db.execute(select(Lesson).where(Lesson.id == data.lesson_id))
    lesson = lesson_result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)

    # Группируем оценки по студентам для проверки слотов
    grades_by_student: dict[UUID, list] = {}
    for grade_item in data.grades:
        if grade_item.student_id not in grades_by_student:
            grades_by_student[grade_item.student_id] = []
        grades_by_student[grade_item.student_id].append(grade_item)

    # Валидируем слоты (batch)
    if lesson.lesson_type == LessonType.LAB:
        from app.services.attestation.lab_slot_validator_batch import (
            get_grades_count_on_lesson_batch,
            get_max_labs_per_lesson_batch,
        )

        student_ids = list(grades_by_student.keys())

        current_counts = await get_grades_count_on_lesson_batch(db, student_ids, data.lesson_id)
        max_allowed_labs = await get_max_labs_per_lesson_batch(db, student_ids, lesson.subject_id, lesson)

        for student_id, student_grades in grades_by_student.items():
            current_count = current_counts.get(student_id, 0)
            max_allowed = max_allowed_labs.get(student_id, 1)
            new_grades_count = len(student_grades)

            if current_count + new_grades_count > max_allowed:
                raise HTTPException(
                    status_code=400, detail=f"Лимит лаб за занятие: {max_allowed} (уже сдано: {current_count})"
                )

    # Валидируем дедлайны (batch)
    from app.services.attestation.deadline_validator_batch import get_max_allowed_grades_batch

    grade_items = [(g.student_id, g.work_number) for g in data.grades]
    max_grades = await get_max_allowed_grades_batch(db, lesson, grade_items)

    for grade_item in data.grades:
        key = (grade_item.student_id, grade_item.work_number)
        max_allowed = max_grades.get(key, 5)
        try:
            validate_grade_for_max(grade_item.grade, max_allowed)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Студент {grade_item.student_id}: {str(e)}")

    # Bulk upsert
    from app.crud.crud_lesson_grade import bulk_upsert_lesson_grades

    grades_data = [
        {"student_id": g.student_id, "grade": g.grade, "work_number": g.work_number, "comment": g.comment}
        for g in data.grades
    ]
    updated = await bulk_upsert_lesson_grades(
        db, data.lesson_id, grades_data, created_by=current_user.id, group_id=lesson.group_id
    )

    # Синхронизация с work_submission для лаб
    synced_count = 0
    if lesson.lesson_type == LessonType.LAB:
        for grade_item in data.grades:
            if grade_item.work_number:
                await journal_sync.sync_from_journal(
                    db,
                    grade_item.student_id,
                    lesson,
                    grade_item.work_number,
                    grade_item.grade,
                    grade_item.comment,
                    current_user.id,
                )
                synced_count += 1

        logger.info(f"[grades_bulk:bulk_update_grades] Synced {synced_count} submissions for lesson {data.lesson_id}")

    await db.commit()
    logger.info(f"Bulk updated {len(updated)} grades for lesson {data.lesson_id}")
    return {"updated": len(updated)}
