"""
Сервис генерации занятий из расписания.
"""

import logging
from datetime import date, timedelta
from typing import cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_schedule import lesson as lesson_crud
from app.crud.crud_schedule import schedule as schedule_crud
from app.models.lesson import Lesson
from app.models.schedule import DayOfWeek, WeekParity
from app.services.schedule_constants import WEEKDAY_SUNDAY
from app.services.schedule_offering_resolution import ResolvedOfferingScope, resolve_schedule_offering_scope

logger = logging.getLogger(__name__)

# Маппинг дней недели Python -> enum
WEEKDAY_MAP = {
    0: DayOfWeek.MONDAY,
    1: DayOfWeek.TUESDAY,
    2: DayOfWeek.WEDNESDAY,
    3: DayOfWeek.THURSDAY,
    4: DayOfWeek.FRIDAY,
    5: DayOfWeek.SATURDAY,
}


class LessonGenerator:
    """Генерация занятий из расписания"""

    async def generate_lessons_for_period(
        self, db: AsyncSession, group_id: UUID, start_date: date, end_date: date
    ) -> list[Lesson]:
        """
        Генерирует занятия на период по расписанию.
        Учитывает:
        - День недели
        - Чётность недели
        - Период действия расписания
        """
        schedule_items = await schedule_crud.get_by_group(db, group_id, active_only=True)

        if not schedule_items:
            logger.warning(f"No schedule items for group {group_id}")
            return []

        lessons = []
        current = start_date

        while current <= end_date:
            weekday = current.weekday()
            if weekday > WEEKDAY_SUNDAY - 1:  # Воскресенье пропускаем
                current += timedelta(days=1)
                continue

            day_of_week = WEEKDAY_MAP.get(weekday)
            if not day_of_week:
                current += timedelta(days=1)
                continue

            # Определяем чётность недели
            week_number = current.isocalendar()[1]
            week_parity = WeekParity.ODD if week_number % 2 else WeekParity.EVEN

            for item in schedule_items:
                # Проверяем день недели
                if item.day_of_week != day_of_week:
                    continue

                # Проверяем чётность недели
                if item.week_parity and item.week_parity != week_parity:
                    continue

                # Проверяем период действия
                if item.start_date > current:
                    continue
                if item.end_date and item.end_date < current:
                    continue

                scope = await self._resolve_item_scope_for_date(db, group_id=group_id, item=item, lesson_date=current)
                if scope is None:
                    continue

                # Создаём занятие (если не существует)
                lesson = await lesson_crud.get_or_create(
                    db,
                    group_id=group_id,
                    schedule_item_id=cast(UUID, item.id),
                    date=current,
                    lesson_number=item.lesson_number,
                    lesson_type=item.lesson_type,
                    subject_id=scope.subject_id,
                    offering_id=scope.offering_id,
                    subgroup=item.subgroup,
                )
                if lesson:
                    lessons.append(lesson)

            current += timedelta(days=1)

        logger.info(f"Generated {len(lessons)} lessons for group {group_id}")
        return lessons

    async def _resolve_item_scope_for_date(
        self,
        db: AsyncSession,
        *,
        group_id: UUID,
        item,
        lesson_date: date,
    ) -> ResolvedOfferingScope | None:
        require_existing = item.subject_id is not None or item.offering_id is not None
        if not require_existing:
            return ResolvedOfferingScope(subject_id=None, offering_id=None)

        try:
            return await resolve_schedule_offering_scope(
                db,
                group_id=group_id,
                reference_date=lesson_date,
                subject_id=item.subject_id,
                offering_id=item.offering_id,
                require_existing=True,
            )
        except ValueError:
            if item.subject_id is None or item.offering_id is None:
                logger.warning(
                    "schedule_item_scope_invalid item_id=%s group_id=%s lesson_date=%s subject_id=%s offering_id=%s",
                    item.id,
                    group_id,
                    lesson_date,
                    item.subject_id,
                    item.offering_id,
                )
                return None

        logger.warning(
            "schedule_item_stale_offering_fallback item_id=%s group_id=%s lesson_date=%s offering_id=%s",
            item.id,
            group_id,
            lesson_date,
            item.offering_id,
        )
        try:
            return await resolve_schedule_offering_scope(
                db,
                group_id=group_id,
                reference_date=lesson_date,
                subject_id=item.subject_id,
                offering_id=None,
                require_existing=True,
            )
        except ValueError:
            logger.warning(
                "schedule_item_scope_unresolved_after_fallback item_id=%s group_id=%s lesson_date=%s subject_id=%s",
                item.id,
                group_id,
                lesson_date,
                item.subject_id,
            )
            return None


lesson_generator = LessonGenerator()
