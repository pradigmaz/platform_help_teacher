"""Проверка текущей лабораторной сессии по расписанию."""

from datetime import datetime
from datetime import time as dt_time
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.services.schedule_constants import MSK_TZ, TIME_TO_LESSON_NUMBER

LAB_SESSION_TYPES = (LessonType.LAB, LessonType.PRACTICE)


def _get_current_lesson_number(now: datetime) -> int | None:
    current_time = now.time()
    for time_range, lesson_num in TIME_TO_LESSON_NUMBER.items():
        start_str, end_str = time_range.split("-")
        start_h, start_m = map(int, start_str.split(":"))
        end_h, end_m = map(int, end_str.split(":"))

        start_time = dt_time(start_h, start_m)
        end_time = dt_time(end_h, end_m)

        if start_time <= current_time <= end_time:
            return lesson_num
    return None


async def get_current_lab_session(
    db: AsyncSession, group_id: UUID, subgroup: int | None, subject_id: UUID | None = None
) -> Lesson | None:
    """Найти текущее lab/practice-занятие для студента."""
    now = datetime.now(MSK_TZ)
    today = now.date()
    current_lesson_number = _get_current_lesson_number(now)
    if current_lesson_number is None:
        return None

    filters = [
        Lesson.group_id == group_id,
        Lesson.date == today,
        Lesson.lesson_number == current_lesson_number,
        Lesson.lesson_type.in_(LAB_SESSION_TYPES),
        Lesson.is_cancelled.is_(False),
    ]

    if subgroup is not None:
        filters.append((Lesson.subgroup.is_(None)) | (Lesson.subgroup == subgroup))

    if subject_id:
        filters.append(Lesson.subject_id == subject_id)

    query = select(Lesson).where(and_(*filters)).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def is_lab_session_now(
    db: AsyncSession, group_id: UUID, subgroup: int | None, subject_id: UUID | None = None
) -> bool:
    """
    Проверить идёт ли сейчас лабораторное занятие для студента.

    Условия:
    - Сегодняшняя дата
    - Текущее время попадает в интервал пары
    - Тип занятия = LAB или PRACTICE
    - Группа и подгруппа совпадают
    - Занятие не отменено
    """
    return await get_current_lab_session(db, group_id, subgroup, subject_id) is not None
