"""
API endpoints для оценок журнала.
"""

import logging
from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_teacher, get_db
from app.core import error_messages as em
from app.models import Lesson, LessonGrade, User
from app.schemas.lesson_grade import LessonGradeCreate, LessonGradeResponse, LessonGradeUpdate
from app.services.attestation.deadline_validator import get_max_allowed_grade
from app.services.journal_grade_write_service import (
    GradeWriteConflictError,
    GradeWriteValidationError,
    journal_grade_write_service,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/grades")
async def get_journal_grades(
    lesson_ids: list[UUID] = Query(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Получить оценки для списка занятий."""
    if not lesson_ids:
        return []

    result = await db.execute(
        select(LessonGrade).where(LessonGrade.lesson_id.in_(lesson_ids)).options(selectinload(LessonGrade.student))
    )
    grades = result.scalars().all()

    grouped: dict[tuple[str, str], list[LessonGrade]] = defaultdict(list)
    for grade in grades:
        grouped[(str(grade.lesson_id), str(grade.student_id))].append(grade)

    payload = []
    for group in grouped.values():
        first = group[0]
        has_conflict = len(group) > 1
        payload.append(
            {
                "id": None if has_conflict else str(first.id),
                "lesson_id": str(first.lesson_id),
                "student_id": str(first.student_id),
                "student_name": first.student.full_name if first.student else None,
                "work_number": None if has_conflict else first.work_number,
                "grade": None if has_conflict else first.grade,
                "comment": None if has_conflict else first.comment,
                "has_conflict": has_conflict,
                "conflict_count": len(group),
            }
        )
    return payload


@router.post("/grades", response_model=LessonGradeResponse)
async def create_grade(
    data: LessonGradeCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_teacher)
):
    """Создать оценку через канонический write-path."""
    lesson_result = await db.execute(select(Lesson).where(Lesson.id == data.lesson_id))
    lesson = lesson_result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)

    # lesson.lesson_type remains the source for LAB-only rules inside the canonical service.
    try:
        grade = await journal_grade_write_service.upsert_grade(
            db=db,
            lesson=lesson,
            student_id=data.student_id,
            grade=data.grade,
            work_number=data.work_number,
            comment=data.comment,
            actor_id=current_user.id,
        )
    except GradeWriteConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except GradeWriteValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    await db.refresh(grade)
    return grade


@router.patch("/grades/{grade_id}", response_model=LessonGradeResponse)
async def update_grade(
    grade_id: UUID,
    data: LessonGradeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Обновить оценку через канонический write-path."""
    existing_result = await db.execute(
        select(LessonGrade).options(selectinload(LessonGrade.lesson)).where(LessonGrade.id == grade_id)
    )
    existing = existing_result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail=em.GRADE_NOT_FOUND)

    field_set = data.model_fields_set
    next_grade = data.grade if "grade" in field_set and data.grade is not None else existing.grade
    next_work_number = data.work_number if "work_number" in field_set else existing.work_number
    next_comment = data.comment if "comment" in field_set else existing.comment

    # lesson.lesson_type remains the source for LAB-only rules inside the canonical service.
    try:
        updated_grade = await journal_grade_write_service.replace_grade(
            db=db,
            existing=existing,
            grade=next_grade,
            work_number=next_work_number,
            comment=next_comment,
            actor_id=current_user.id,
        )
    except GradeWriteConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except GradeWriteValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    await db.refresh(updated_grade)
    return updated_grade


@router.delete("/grades/{grade_id}")
async def delete_grade(
    grade_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_teacher)
):
    """Удалить оценку."""
    # delete_lesson_grade legacy path is superseded by the canonical grade write service.
    result = await db.execute(
        select(LessonGrade).options(selectinload(LessonGrade.lesson)).where(LessonGrade.id == grade_id)
    )
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail=em.GRADE_NOT_FOUND)

    await journal_grade_write_service.delete_grade(db, grade, current_user.id)
    await db.commit()
    return {"deleted": True}


@router.delete("/grades")
async def delete_grade_by_lesson_student(
    lesson_id: UUID = Query(...),
    student_id: UUID = Query(...),
    work_number: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Удалить оценку по lesson_id и student_id (опционально work_number)."""
    conditions = [LessonGrade.lesson_id == lesson_id, LessonGrade.student_id == student_id]
    if work_number is not None:
        conditions.append(LessonGrade.work_number == work_number)

    result = await db.execute(select(LessonGrade).options(selectinload(LessonGrade.lesson)).where(and_(*conditions)))
    grades = result.scalars().all()

    if not grades:
        return {"deleted": False, "message": "Grade not found"}

    if len(grades) > 1 and work_number is None:
        raise HTTPException(
            status_code=409,
            detail=f"Студент имеет {len(grades)} оценок на этом занятии. Укажите work_number для удаления конкретной.",
        )

    grade = grades[0]
    await journal_grade_write_service.delete_grade(db, grade, current_user.id)
    await db.commit()
    logger.info(f"Deleted grade for lesson {lesson_id}, student {student_id}, work_number={work_number}")
    return {"deleted": True}


@router.get("/grades/max-allowed/{lesson_id}")
async def get_lesson_max_grade(
    lesson_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_teacher)
):
    """Получить максимально допустимую оценку для занятия с учётом дедлайна."""
    lesson_result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = lesson_result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)

    max_allowed = await get_max_allowed_grade(db, lesson)
    return {"lesson_id": str(lesson_id), "max_allowed_grade": max_allowed}
