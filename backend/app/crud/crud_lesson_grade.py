"""
CRUD операции для оценок за занятия.
"""
import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lesson_grade import LessonGrade

logger = logging.getLogger(__name__)


async def create_lesson_grade(
    db: AsyncSession,
    lesson_id: UUID,
    student_id: UUID,
    grade: int,
    work_number: Optional[int] = None,
    comment: Optional[str] = None,
    created_by: Optional[UUID] = None
) -> LessonGrade:
    """Создать оценку за занятие."""
    lesson_grade = LessonGrade(
        lesson_id=lesson_id,
        student_id=student_id,
        grade=grade,
        work_number=work_number,
        comment=comment,
        created_by=created_by
    )
    db.add(lesson_grade)
    await db.commit()
    await db.refresh(lesson_grade)
    logger.info(f"Created lesson grade: lesson={lesson_id}, student={student_id}, grade={grade}")
    return lesson_grade


async def get_lesson_grade(
    db: AsyncSession,
    grade_id: UUID
) -> Optional[LessonGrade]:
    """Получить оценку по ID."""
    result = await db.execute(
        select(LessonGrade).where(LessonGrade.id == grade_id)
    )
    return result.scalar_one_or_none()


async def get_lesson_grades_by_lesson(
    db: AsyncSession,
    lesson_id: UUID
) -> List[LessonGrade]:
    """Получить все оценки за занятие."""
    result = await db.execute(
        select(LessonGrade)
        .where(LessonGrade.lesson_id == lesson_id)
        .options(selectinload(LessonGrade.student))
    )
    return list(result.scalars().all())


async def get_lesson_grades_by_student(
    db: AsyncSession,
    student_id: UUID,
    lesson_ids: Optional[List[UUID]] = None
) -> List[LessonGrade]:
    """Получить оценки студента (опционально по списку занятий)."""
    query = select(LessonGrade).where(LessonGrade.student_id == student_id)
    if lesson_ids:
        query = query.where(LessonGrade.lesson_id.in_(lesson_ids))
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_student_lesson_grade(
    db: AsyncSession,
    lesson_id: UUID,
    student_id: UUID,
    work_number: Optional[int] = None
) -> Optional[LessonGrade]:
    """Получить оценку студента за конкретное занятие и работу."""
    conditions = [
        LessonGrade.lesson_id == lesson_id,
        LessonGrade.student_id == student_id
    ]
    if work_number is not None:
        conditions.append(LessonGrade.work_number == work_number)
    else:
        conditions.append(LessonGrade.work_number.is_(None))
    
    result = await db.execute(
        select(LessonGrade).where(and_(*conditions))
    )
    return result.scalar_one_or_none()


async def update_lesson_grade(
    db: AsyncSession,
    grade_id: UUID,
    grade: Optional[int] = None,
    work_number: Optional[int] = None,
    comment: Optional[str] = None
) -> Optional[LessonGrade]:
    """Обновить оценку."""
    lesson_grade = await get_lesson_grade(db, grade_id)
    if not lesson_grade:
        return None
    
    if grade is not None:
        lesson_grade.grade = grade
    if work_number is not None:
        lesson_grade.work_number = work_number
    if comment is not None:
        lesson_grade.comment = comment
    
    await db.commit()
    await db.refresh(lesson_grade)
    logger.info(f"Updated lesson grade: {grade_id}")
    return lesson_grade


async def delete_lesson_grade(
    db: AsyncSession,
    grade_id: UUID
) -> bool:
    """Удалить оценку."""
    lesson_grade = await get_lesson_grade(db, grade_id)
    if not lesson_grade:
        return False
    
    await db.delete(lesson_grade)
    await db.commit()
    logger.info(f"Deleted lesson grade: {grade_id}")
    return True


async def upsert_lesson_grade(
    db: AsyncSession,
    lesson_id: UUID,
    student_id: UUID,
    grade: int,
    work_number: Optional[int] = None,
    comment: Optional[str] = None,
    created_by: Optional[UUID] = None
) -> LessonGrade:
    """Создать или обновить оценку."""
    existing = await get_student_lesson_grade(db, lesson_id, student_id, work_number)
    
    if existing:
        existing.grade = grade
        if comment is not None:
            existing.comment = comment
        await db.commit()
        await db.refresh(existing)
        return existing
    
    return await create_lesson_grade(
        db, lesson_id, student_id, grade, work_number, comment, created_by
    )
