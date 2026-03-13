"""
Bulk операции с оценками (оптимизированные batch-запросы).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_teacher, get_db
from app.core import error_messages as em
from app.core.limiter import limiter
from app.models import Lesson, User
from app.schemas.lesson_grade import BulkGradeCreate
from app.services.journal_grade_write_service import (
    GradeWriteConflictError,
    GradeWriteValidationError,
    journal_grade_write_service,
)

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
    """Массовое создание/обновление оценок через канонический write-path."""
    lesson_result = await db.execute(select(Lesson).where(Lesson.id == data.lesson_id))
    lesson = lesson_result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)

    # lesson.lesson_type remains the source for LAB-only rules inside the canonical service.
    updated = []
    try:
        for grade_item in data.grades:
            grade = await journal_grade_write_service.upsert_grade(
                db=db,
                lesson=lesson,
                student_id=grade_item.student_id,
                grade=grade_item.grade,
                work_number=grade_item.work_number,
                comment=grade_item.comment,
                actor_id=current_user.id,
            )
            updated.append(grade)
    except GradeWriteConflictError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except GradeWriteValidationError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    logger.info(f"Bulk updated {len(updated)} grades for lesson {data.lesson_id}")
    return {"updated": len(updated)}
