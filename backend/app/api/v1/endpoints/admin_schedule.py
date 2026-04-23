"""API эндпоинты для управления расписанием и занятиями."""

from datetime import date
from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core import error_messages as em
from app.crud.crud_schedule import lesson as crud_lesson
from app.crud.crud_schedule import schedule as crud_schedule
from app.db.session import get_db
from app.models import User
from app.models.schedule import LessonType
from app.schemas.schedule import (
    GenerateLessonsRequest,
    GenerateLessonsResponse,
    LessonCreate,
    LessonResponse,
    LessonUpdate,
    ScheduleItemCreate,
    ScheduleItemResponse,
    ScheduleItemUpdate,
)
from app.services.lesson_generator import lesson_generator
from app.services.schedule_offering_resolution import (
    combine_resolved_scopes,
    resolve_schedule_offering_scope,
    resolve_schedule_scope_from_item,
    validate_schedule_item_date_range,
)

router = APIRouter()


@router.post("/groups/{group_id}/schedule", response_model=ScheduleItemResponse)
async def create_schedule_item(
    group_id: UUID,
    item_in: ScheduleItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Создать элемент расписания."""
    try:
        validate_schedule_item_date_range(
            start_date=item_in.start_date,
            end_date=item_in.end_date,
            subject_id=item_in.subject_id,
            offering_id=item_in.offering_id,
        )
        scope = await resolve_schedule_offering_scope(
            db,
            group_id=group_id,
            reference_date=item_in.start_date,
            subject_id=item_in.subject_id,
            offering_id=item_in.offering_id,
            require_existing=item_in.subject_id is not None or item_in.offering_id is not None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    item = await crud_schedule.create(
        db,
        group_id=group_id,
        day_of_week=item_in.day_of_week,
        lesson_number=item_in.lesson_number,
        lesson_type=item_in.lesson_type,
        subject=item_in.subject,
        subject_id=scope.subject_id,
        offering_id=scope.offering_id,
        room=item_in.room,
        teacher_id=item_in.teacher_id,
        start_date=item_in.start_date,
        end_date=item_in.end_date,
        week_parity=item_in.week_parity,
        subgroup=item_in.subgroup,
    )
    return item


@router.get("/groups/{group_id}/schedule", response_model=list[ScheduleItemResponse])
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
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)

    payload = item_in.model_dump(exclude_unset=True)
    try:
        validate_schedule_item_date_range(
            start_date=payload.get("start_date", item.start_date),
            end_date=payload.get("end_date", item.end_date),
            subject_id=payload.get("subject_id", item.subject_id),
            offering_id=payload.get("offering_id", item.offering_id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if {"subject_id", "offering_id", "start_date"} & payload.keys():
        try:
            scope = await resolve_schedule_offering_scope(
                db,
                group_id=cast(UUID, item.group_id),
                reference_date=payload.get("start_date", item.start_date),
                subject_id=payload.get("subject_id", item.subject_id),
                offering_id=payload.get("offering_id", item.offering_id),
                require_existing=(
                    payload.get("subject_id", item.subject_id) is not None
                    or payload.get("offering_id", item.offering_id) is not None
                ),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        payload["subject_id"] = scope.subject_id
        payload["offering_id"] = scope.offering_id

    item = await crud_schedule.update(db, db_obj=item, **payload)
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
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)
    return {"status": "deleted"}


@router.post("/lessons", response_model=LessonResponse)
async def create_lesson(
    lesson_in: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Создать занятие вручную."""
    try:
        explicit_scope = await resolve_schedule_offering_scope(
            db,
            group_id=lesson_in.group_id,
            reference_date=lesson_in.date,
            subject_id=lesson_in.subject_id,
            offering_id=lesson_in.offering_id,
            require_existing=lesson_in.subject_id is not None or lesson_in.offering_id is not None,
        )
        linked_scope = await resolve_schedule_scope_from_item(
            db,
            group_id=lesson_in.group_id,
            reference_date=lesson_in.date,
            schedule_item_id=lesson_in.schedule_item_id,
        )
        scope = combine_resolved_scopes(explicit_scope, linked_scope)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    lesson = await crud_lesson.create(
        db,
        group_id=lesson_in.group_id,
        schedule_item_id=lesson_in.schedule_item_id,
        date=lesson_in.date,
        lesson_number=lesson_in.lesson_number,
        lesson_type=lesson_in.lesson_type,
        subject_id=scope.subject_id,
        offering_id=scope.offering_id,
        topic=lesson_in.topic,
        room=lesson_in.room,
        work_id=lesson_in.work_id,
        subgroup=lesson_in.subgroup,
    )
    return lesson


@router.get("/groups/{group_id}/lessons", response_model=list[LessonResponse])
async def get_lessons(
    group_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    lesson_type: LessonType | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить занятия группы за период."""
    lessons = await crud_lesson.get_by_group_and_period(db, group_id, start_date, end_date, lesson_type)
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
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)
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
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)

    payload = lesson_in.model_dump(exclude_unset=True)
    if {"subject_id", "offering_id"} & payload.keys():
        try:
            scope = await resolve_schedule_offering_scope(
                db,
                group_id=lesson.group_id,
                reference_date=lesson.date,
                subject_id=payload.get("subject_id"),
                offering_id=payload.get("offering_id"),
                require_existing=payload.get("subject_id") is not None or payload.get("offering_id") is not None,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        payload["subject_id"] = scope.subject_id
        payload["offering_id"] = scope.offering_id

    lesson = await crud_lesson.update(db, db_obj=lesson, **payload)
    return lesson


@router.post("/lessons/{lesson_id}/cancel", response_model=LessonResponse)
async def cancel_lesson(
    lesson_id: UUID,
    reason: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Отменить занятие."""
    lesson = await crud_lesson.get(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)

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
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)
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
    lessons = await lesson_generator.generate_lessons_for_period(db, group_id, request.start_date, request.end_date)
    return GenerateLessonsResponse(
        created_count=len(lessons), lessons=[LessonResponse.model_validate(l) for l in lessons]
    )
