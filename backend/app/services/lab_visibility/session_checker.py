"""Проверка текущей лабораторной сессии по расписанию."""
from datetime import datetime, time as dt_time
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.services.schedule_constants import TIME_TO_LESSON_NUMBER, MSK_TZ


async def is_lab_session_now(
    db: AsyncSession,
    group_id: UUID,
    subgroup: Optional[int],
    subject_id: Optional[UUID] = None
) -> bool:
    """
    Проверить идёт ли сейчас лабораторное занятие для студента.

    Условия:
    - Сегодняшняя дата
    - Текущее время попадает в интервал пары
    - Тип занятия = LAB
    - Группа и подгруппа совпадают
    - Занятие не отменено
    """
    now = datetime.now(MSK_TZ)
    today = now.date()
    current_time = now.time()

    # Определяем номер текущей пары по времени
    current_lesson_number = None
    for time_range, lesson_num in TIME_TO_LESSON_NUMBER.items():
        start_str, end_str = time_range.split('-')
        start_h, start_m = map(int, start_str.split(':'))
        end_h, end_m = map(int, end_str.split(':'))

        start_time = dt_time(start_h, start_m)
        end_time = dt_time(end_h, end_m)

        if start_time <= current_time <= end_time:
            current_lesson_number = lesson_num
            break

    if current_lesson_number is None:
        return False

    # Ищем занятие
    filters = [
        Lesson.group_id == group_id,
        Lesson.date == today,
        Lesson.lesson_number == current_lesson_number,
        Lesson.lesson_type == LessonType.LAB,
        Lesson.is_cancelled == False,
    ]

    if subgroup is not None:
        filters.append((Lesson.subgroup == None) | (Lesson.subgroup == subgroup))

    if subject_id:
        filters.append(Lesson.subject_id == subject_id)

    query = select(Lesson.id).where(and_(*filters)).limit(1)
    result = await db.execute(query)

    return result.scalar_one_or_none() is not None
