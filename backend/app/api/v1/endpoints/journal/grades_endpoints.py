"""
API endpoints для оценок журнала.
"""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_teacher
from app.core import error_messages as em
from app.models import User, Lesson, LessonGrade
from app.schemas.lesson_grade import (
    LessonGradeCreate, LessonGradeUpdate, LessonGradeResponse, 
    BulkGradeCreate
)
from app.crud import crud_lesson_grade
from app.core.limiter import limiter
from app.services.attestation.deadline_validator import get_max_allowed_grade, validate_grade_for_max
from app.services.attestation.lab_slot_validator import validate_lab_submission
from app.services import submission_journal_sync as journal_sync

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/grades")
async def get_journal_grades(
    lesson_ids: List[UUID] = Query(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получить оценки для списка занятий."""
    if not lesson_ids:
        return []
    
    result = await db.execute(
        select(LessonGrade)
        .where(LessonGrade.lesson_id.in_(lesson_ids))
        .options(selectinload(LessonGrade.student))
    )
    grades = result.scalars().all()
    
    return [
        {
            "id": str(g.id),
            "lesson_id": str(g.lesson_id),
            "student_id": str(g.student_id),
            "student_name": g.student.full_name if g.student else None,
            "work_number": g.work_number,
            "grade": g.grade,
            "comment": g.comment,
        }
        for g in grades
    ]


@router.post("/grades", response_model=LessonGradeResponse)
async def create_grade(
    data: LessonGradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Создать оценку с проверкой дедлайна и слотов."""
    lesson_result = await db.execute(select(Lesson).where(Lesson.id == data.lesson_id))
    lesson = lesson_result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)
    
    # Проверяем слоты (1 лаба = 1 пара, +1 для EXCUSED)
    if lesson.lesson_type == 'LAB':
        try:
            await validate_lab_submission(
                db, data.student_id, data.lesson_id, lesson.subject_id, data.work_number, lesson
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Проверяем дедлайн
    max_allowed = await get_max_allowed_grade(
        db, lesson, student_id=data.student_id, work_number=data.work_number
    )
    try:
        validate_grade_for_max(data.grade, max_allowed)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    grade = await crud_lesson_grade.upsert_lesson_grade(
        db,
        lesson_id=data.lesson_id,
        student_id=data.student_id,
        grade=data.grade,
        work_number=data.work_number,
        comment=data.comment,
        created_by=current_user.id,
        group_id=lesson.group_id
    )
    
    # Синхронизация с work_submission для лаб
    if data.work_number and lesson.lesson_type == 'LAB':
        logger.info(f"[grades_endpoints:create_grade] Syncing to work_submission: student={data.student_id}, work={data.work_number}, grade={data.grade}")
        await journal_sync.sync_from_journal(
            db, data.student_id, lesson, data.work_number,
            data.grade, data.comment, current_user.id
        )
    
    return grade


@router.patch("/grades/{grade_id}", response_model=LessonGradeResponse)
async def update_grade(
    grade_id: UUID,
    data: LessonGradeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Обновить оценку с проверкой дедлайна."""
    existing_result = await db.execute(
        select(LessonGrade)
        .options(selectinload(LessonGrade.lesson))
        .where(LessonGrade.id == grade_id)
    )
    existing = existing_result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail=em.GRADE_NOT_FOUND)
    
    if data.grade is not None and existing.lesson:
        max_allowed = await get_max_allowed_grade(
            db, existing.lesson, 
            student_id=existing.student_id, 
            work_number=data.work_number or existing.work_number
        )
        try:
            validate_grade_for_max(data.grade, max_allowed)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    grade = await crud_lesson_grade.update_lesson_grade(
        db,
        grade_id=grade_id,
        grade=data.grade,
        work_number=data.work_number,
        comment=data.comment
    )
    if not grade:
        raise HTTPException(status_code=404, detail=em.GRADE_NOT_FOUND)
    
    # Синхронизация с work_submission для лаб
    work_number = data.work_number if data.work_number is not None else existing.work_number
    if work_number and existing.lesson and existing.lesson.lesson_type == 'LAB':
        final_grade = data.grade if data.grade is not None else existing.grade
        final_comment = data.comment if data.comment is not None else existing.comment
        logger.info(f"[grades_endpoints:update_grade] Syncing to work_submission: student={existing.student_id}, work={work_number}, grade={final_grade}")
        await journal_sync.sync_from_journal(
            db,
            existing.student_id,
            existing.lesson,
            work_number,
            final_grade,
            final_comment,
            current_user.id
        )
    
    return grade


@router.delete("/grades/{grade_id}")
async def delete_grade(
    grade_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Удалить оценку."""
    success = await crud_lesson_grade.delete_lesson_grade(db, grade_id)
    if not success:
        raise HTTPException(status_code=404, detail=em.GRADE_NOT_FOUND)
    return {"deleted": True}


@router.delete("/grades")
async def delete_grade_by_lesson_student(
    lesson_id: UUID = Query(...),
    student_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Удалить оценку по lesson_id и student_id."""
    result = await db.execute(
        select(LessonGrade).where(and_(
            LessonGrade.lesson_id == lesson_id,
            LessonGrade.student_id == student_id
        ))
    )
    grade = result.scalar_one_or_none()
    if not grade:
        return {"deleted": False, "message": "Grade not found"}
    
    await db.delete(grade)
    await db.commit()
    logger.info(f"Deleted grade for lesson {lesson_id}, student {student_id}")
    return {"deleted": True}


@router.get("/grades/max-allowed/{lesson_id}")
async def get_lesson_max_grade(
    lesson_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получить максимально допустимую оценку для занятия с учётом дедлайна."""
    lesson_result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = lesson_result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)
    
    max_allowed = await get_max_allowed_grade(db, lesson)
    return {"lesson_id": str(lesson_id), "max_allowed_grade": max_allowed}
