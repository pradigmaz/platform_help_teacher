"""Aggregate admin schedule view endpoint."""

from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps as api_deps
from app.api.deps import get_current_teacher, get_db
from app.core import error_messages as em
from app.crud import crud_parse_history, crud_schedule_parser
from app.crud.crud_schedule import lesson as crud_lesson
from app.models import User
from app.models.schedule import LessonType
from app.schemas.schedule import (
    GroupedLectureGroupResponse,
    GroupedLectureResponse,
    LessonResponse,
    ScheduleParseStatusResponse,
    ScheduleViewResponse,
)
from app.schemas.schedule_parser import ScheduleConflictResponse
from app.services.schedule_attendance_summary import (
    grouped_lecture_item_key,
    schedule_attendance_summary_service,
)

router = APIRouter()


@router.get("/lectures/grouped")
async def get_grouped_lectures(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(api_deps.get_current_active_superuser),
):
    """Получить лекции сгруппированные по (дата + пара + предмет)."""
    return await crud_lesson.get_grouped_lectures(db, start_date, end_date)


@router.get("/groups/{group_id}/students")
async def get_group_students(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(api_deps.get_current_active_superuser),
):
    """Получить студентов группы для журнала."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.group import Group

    result = await db.execute(select(Group).options(selectinload(Group.users)).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail=em.GROUP_NOT_FOUND)

    students = sorted([u for u in group.users if u.is_active], key=lambda u: u.full_name)
    return [{"id": str(s.id), "full_name": s.full_name} for s in students]


@router.get("/schedule/view", response_model=ScheduleViewResponse)
async def get_schedule_view(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
) -> ScheduleViewResponse:
    parse_status = await _get_parse_status(db, current_user)
    conflicts = await crud_schedule_parser.get_unresolved_conflicts(db, current_user.id)

    lesson_rows = await _get_non_lecture_lessons(db, start_date, end_date)
    grouped_lectures = await crud_lesson.get_grouped_lectures(db, start_date, end_date)
    summary_result = await schedule_attendance_summary_service.build(
        db,
        regular_lessons=lesson_rows,
        grouped_lecture_items=grouped_lectures,
    )

    return ScheduleViewResponse(
        parse_status=parse_status,
        conflicts=[ScheduleConflictResponse.model_validate(conflict) for conflict in conflicts],
        lessons=[
            LessonResponse(
                id=row.id,
                group_id=row.group_id,
                schedule_item_id=row.schedule_item_id,
                date=row.date,
                lesson_number=row.lesson_number,
                lesson_type=row.lesson_type,
                topic=row.topic,
                room=row.room,
                work_id=row.work_id,
                work_number=row.work_number,
                subgroup=row.subgroup,
                is_cancelled=row.is_cancelled,
                cancellation_reason=row.cancellation_reason,
                ended_early=row.ended_early,
                subject_name=row.subject.name if row.subject else None,
                group_name=row.group.name if row.group else None,
                summary=summary_result.lesson_summaries.get(row.id),
            )
            for row in lesson_rows
        ],
        grouped_lectures=[
            GroupedLectureResponse(
                date=date.fromisoformat(item["date"]),
                lesson_number=item["lesson_number"],
                subject_id=item["subject_id"],
                subject_name=item["subject_name"],
                topic=item["topic"],
                room=item.get("room"),
                is_cancelled=summary_result.grouped_lecture_summaries[grouped_lecture_item_key(item)].is_cancelled,
                ended_early=summary_result.grouped_lecture_summaries[grouped_lecture_item_key(item)].ended_early,
                groups=[
                    GroupedLectureGroupResponse(
                        id=group["id"],
                        name=group["name"],
                        lesson_id=group["lesson_id"],
                    )
                    for group in item["groups"]
                ],
                summary=summary_result.grouped_lecture_summaries[grouped_lecture_item_key(item)].summary,
            )
            for item in grouped_lectures
        ],
        last_updated=datetime.now(UTC).isoformat(),
    )


async def _get_parse_status(db: AsyncSession, current_user: User) -> ScheduleParseStatusResponse:
    last = await crud_parse_history.get_last_history(db, current_user.id)
    if not last:
        return ScheduleParseStatusResponse(is_running=False, last_run=None)
    return ScheduleParseStatusResponse(
        is_running=last.status == "running",
        status=last.status,
        started_at=last.started_at.isoformat() if last.started_at else None,
        finished_at=last.finished_at.isoformat() if last.finished_at else None,
        lessons_created=last.lessons_created,
        lessons_updated=last.lessons_updated,
        lessons_skipped=last.lessons_skipped,
        conflicts_created=last.conflicts_created,
        error_message=last.error_message,
        last_run=last.finished_at.isoformat() if last.finished_at else None,
    )


async def _get_non_lecture_lessons(db: AsyncSession, start_date: date, end_date: date):
    from sqlalchemy import and_, select
    from sqlalchemy.orm import selectinload

    from app.models import Lesson

    query = (
        select(Lesson)
        .options(selectinload(Lesson.subject), selectinload(Lesson.group))
        .where(and_(Lesson.date >= start_date, Lesson.date <= end_date))
        .where(Lesson.lesson_type != LessonType.LECTURE)
        .order_by(Lesson.date.asc(), Lesson.lesson_number.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())
