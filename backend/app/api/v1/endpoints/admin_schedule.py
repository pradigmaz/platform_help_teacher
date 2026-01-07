"""API эндпоинты для управления расписанием и занятиями."""
from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.models import User
from app.models.schedule import DayOfWeek, LessonType, WeekParity
from app.crud.crud_schedule import schedule as crud_schedule, lesson as crud_lesson
from app.services.lesson_generator import lesson_generator
from app.schemas.schedule import (
    ScheduleItemCreate, ScheduleItemUpdate, ScheduleItemResponse,
    LessonCreate, LessonUpdate, LessonResponse,
    GenerateLessonsRequest, GenerateLessonsResponse
)
from app.core.limiter import limiter

router = APIRouter()


# === Schedule Items ===

@router.post("/groups/{group_id}/schedule", response_model=ScheduleItemResponse)
async def create_schedule_item(
    group_id: UUID,
    item_in: ScheduleItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Создать элемент расписания."""
    item = await crud_schedule.create(
        db,
        group_id=group_id,
        day_of_week=item_in.day_of_week,
        lesson_number=item_in.lesson_number,
        lesson_type=item_in.lesson_type,
        subject=item_in.subject,
        room=item_in.room,
        teacher_id=item_in.teacher_id,
        start_date=item_in.start_date,
        end_date=item_in.end_date,
        week_parity=item_in.week_parity,
        subgroup=item_in.subgroup
    )
    return item


@router.get("/groups/{group_id}/schedule", response_model=List[ScheduleItemResponse])
async def get_schedule(
    group_id: UUID,
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить расписание группы."""
    items = await crud_schedule.get_by_group(db, group_id, active_only=active_only)
    return items


@router.patch("/schedule/{item_id}", response_model=ScheduleItemResponse)
async def update_schedule_item(
    item_id: UUID,
    item_in: ScheduleItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить элемент расписания."""
    item = await crud_schedule.get(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Элемент расписания не найден")
    
    item = await crud_schedule.update(db, db_obj=item, **item_in.model_dump(exclude_unset=True))
    return item


@router.delete("/schedule/{item_id}")
async def delete_schedule_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Удалить элемент расписания."""
    deleted = await crud_schedule.delete(db, id=item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Элемент расписания не найден")
    return {"status": "deleted"}


# === Lessons ===

@router.post("/lessons", response_model=LessonResponse)
async def create_lesson(
    lesson_in: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Создать занятие вручную."""
    lesson = await crud_lesson.create(
        db,
        group_id=lesson_in.group_id,
        schedule_item_id=lesson_in.schedule_item_id,
        date=lesson_in.date,
        lesson_number=lesson_in.lesson_number,
        lesson_type=lesson_in.lesson_type,
        topic=lesson_in.topic,
        work_id=lesson_in.work_id,
        subgroup=lesson_in.subgroup
    )
    return lesson


@router.get("/groups/{group_id}/lessons", response_model=List[LessonResponse])
async def get_lessons(
    group_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    lesson_type: Optional[LessonType] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить занятия группы за период."""
    lessons = await crud_lesson.get_by_group_and_period(
        db, group_id, start_date, end_date, lesson_type
    )
    return lessons


@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить занятие по ID."""
    lesson = await crud_lesson.get(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Занятие не найдено")
    return lesson


@router.patch("/lessons/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: UUID,
    lesson_in: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить занятие."""
    lesson = await crud_lesson.get(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Занятие не найдено")
    
    lesson = await crud_lesson.update(db, db_obj=lesson, **lesson_in.model_dump(exclude_unset=True))
    return lesson


@router.post("/lessons/{lesson_id}/cancel", response_model=LessonResponse)
async def cancel_lesson(
    lesson_id: UUID,
    reason: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Отменить занятие."""
    lesson = await crud_lesson.get(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Занятие не найдено")
    
    lesson = await crud_lesson.cancel(db, db_obj=lesson, reason=reason)
    return lesson


@router.delete("/lessons/{lesson_id}")
async def delete_lesson(
    lesson_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Удалить занятие."""
    deleted = await crud_lesson.delete(db, id=lesson_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Занятие не найдено")
    return {"status": "deleted"}


# === Generate Lessons ===

@router.post("/groups/{group_id}/generate-lessons", response_model=GenerateLessonsResponse)
async def generate_lessons(
    group_id: UUID,
    request: GenerateLessonsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Сгенерировать занятия из расписания на период."""
    lessons = await lesson_generator.generate_lessons_for_period(
        db, group_id, request.start_date, request.end_date
    )
    return GenerateLessonsResponse(
        created_count=len(lessons),
        lessons=[LessonResponse.model_validate(l) for l in lessons]
    )


# === Schedule Parser ===

from pydantic import BaseModel
from app.services.schedule_import_service import ScheduleImportService


class ParseScheduleRequest(BaseModel):
    """Запрос на парсинг расписания"""
    teacher_name: str
    start_date: date
    end_date: Optional[date] = None  # По умолчанию - сегодня


class ParseScheduleResponse(BaseModel):
    """Результат парсинга"""
    total_parsed: int
    groups_created: int
    lessons_created: int
    lessons_skipped: int
    groups: List[str]


@router.post("/schedule/parse", response_model=ParseScheduleResponse)
@limiter.limit("5/hour")
async def parse_schedule(
    request: Request,
    data: ParseScheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Парсинг расписания с kis.vgltu.ru.
    Автоматически создаёт группы и занятия.
    """
    end_date = data.end_date or date.today()
    
    if data.start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date должна быть раньше end_date")
    
    import_service = ScheduleImportService(db)
    
    try:
        stats = await import_service.import_from_parser(
            teacher_name=data.teacher_name,
            start_date=data.start_date,
            end_date=end_date
        )
        
        return ParseScheduleResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка парсинга: {str(e)}")
