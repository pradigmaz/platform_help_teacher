"""Atomic lesson sheet save endpoints for schedule UI."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core import error_messages as em
from app.db.session import get_db
from app.models import Lesson, User
from app.schemas.schedule import (
    GroupedLectureSheetSaveRequest,
    GroupedLectureSheetSaveResponse,
    LessonSheetSaveRequest,
    LessonSheetSaveResponse,
)
from app.services.lesson_sheet_service import LessonSheetValidationError, lesson_sheet_service

router = APIRouter()


@router.post("/lessons/{lesson_id}/sheet", response_model=LessonSheetSaveResponse)
async def save_lesson_sheet(
    lesson_id: UUID,
    payload: LessonSheetSaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Save lesson sheet state atomically for schedule and journal consumers."""
    lesson_result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = lesson_result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)

    try:
        result = await lesson_sheet_service.save_sheet(db, lesson, payload, current_user.id)
    except LessonSheetValidationError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await db.commit()
    await db.refresh(lesson)
    result["lesson"] = lesson
    return result


@router.post("/lectures/grouped/sheet", response_model=GroupedLectureSheetSaveResponse)
async def save_grouped_lecture_sheet(
    payload: GroupedLectureSheetSaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Atomically save grouped lecture attendance/status across all lesson rows."""
    lesson_ids = [item.lesson_id for item in payload.items]
    lessons_result = await db.execute(select(Lesson).where(Lesson.id.in_(lesson_ids)))
    lessons = lessons_result.scalars().all()
    lessons_by_id = {lesson.id: lesson for lesson in lessons}

    if len(lessons_by_id) != len(set(lesson_ids)):
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)

    try:
        result = await lesson_sheet_service.save_grouped_sheet(
            db=db,
            lessons_by_id=lessons_by_id,
            payload=payload,
            actor_id=current_user.id,
        )
    except LessonSheetValidationError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await db.commit()
    return result
