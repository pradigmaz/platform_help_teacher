"""Расчёт видимости и дедлайнов лаб по расписанию."""
import logging
from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.services.lab_visibility.models import LabVisibilityInfo

logger = logging.getLogger(__name__)


def _build_subgroup_filter(subgroup: int | None) -> list:
    """
    Построить фильтр по подгруппе.

    Логика:
    - Занятия для всей группы (subgroup = NULL) видны всем
    - Занятия для конкретной подгруппы видны только студентам этой подгруппы
    - Студент без подгруппы видит ВСЕ занятия (и общие, и по подгруппам)
    """
    if subgroup is not None:
        return [(Lesson.subgroup is None) | (Lesson.subgroup == subgroup)]
    return []


def _build_base_filter(
    group_id: UUID,
    subgroup: int | None,
    subject_id: UUID | None = None
) -> list:
    """Построить базовый фильтр для запросов к занятиям."""
    base_filter = [
        Lesson.group_id == group_id,
        Lesson.lesson_type == LessonType.LAB,
        not Lesson.is_cancelled,
    ]
    base_filter.extend(_build_subgroup_filter(subgroup))
    if subject_id:
        base_filter.append(Lesson.subject_id == subject_id)
    return base_filter


def _calculate_deadline_status(
    labs_after: int,
    effective_deadline: int | None,
    visible_from: date,
    today: date
) -> tuple[str | None, int | None]:
    """
    Рассчитать статус дедлайна и оставшиеся пары.

    Returns:
        (status, lessons_until) — статус ('active'/'expired'/None) и пар до дедлайна.
    """
    if effective_deadline is None:
        return None, None

    if labs_after >= effective_deadline:
        return 'expired', None
    elif visible_from <= today:
        return 'active', effective_deadline - labs_after

    return None, None


async def calculate_visibility_for_subject(
    db: AsyncSession,
    lab_numbers: list[int],
    group_id: UUID,
    subgroup: int | None,
    labs_deadlines: dict[int, tuple],
    subject_id: UUID | None,
    today: date,
    labs_ids: dict[int, UUID] | None = None,
    extensions_map: dict[UUID, int] | None = None
) -> dict[int, LabVisibilityInfo]:
    """Получить visibility для лаб одного предмета."""
    labs_ids = labs_ids or {}
    extensions_map = extensions_map or {}

    base_filter = _build_base_filter(group_id, subgroup, subject_id)

    # 1. MIN/MAX даты для всех лаб одним запросом
    dates_query = select(
        Lesson.work_number,
        func.min(Lesson.date).label('min_date'),
        func.max(Lesson.date).label('max_date')
    ).where(
        and_(*base_filter, Lesson.work_number.in_(lab_numbers))
    ).group_by(Lesson.work_number)

    dates_result = await db.execute(dates_query)
    lab_dates = {row.work_number: (row.min_date, row.max_date) for row in dates_result.all()}

    # 2. Все уникальные work_number с датами для подсчёта дедлайнов
    all_labs_query = select(
        Lesson.work_number,
        func.min(Lesson.date).label('first_date')
    ).where(
        and_(*base_filter, Lesson.work_number is not None, Lesson.date <= today)
    ).group_by(Lesson.work_number).order_by(func.min(Lesson.date))

    all_labs_result = await db.execute(all_labs_query)
    all_labs_ordered = [(row.work_number, row.first_date) for row in all_labs_result.all()]

    # 3. Строим результат для каждой лабы
    result = {}
    for lab_number in lab_numbers:
        result[lab_number] = _calculate_single_lab_visibility(
            lab_number=lab_number,
            lab_dates=lab_dates,
            all_labs_ordered=all_labs_ordered,
            labs_deadlines=labs_deadlines,
            labs_ids=labs_ids,
            extensions_map=extensions_map,
            today=today
        )

    return result


def _calculate_single_lab_visibility(
    lab_number: int,
    lab_dates: dict[int, tuple[date, date]],
    all_labs_ordered: list[tuple[int, date]],
    labs_deadlines: dict[int, tuple],
    labs_ids: dict[int, UUID],
    extensions_map: dict[UUID, int],
    today: date
) -> LabVisibilityInfo:
    """Рассчитать видимость и дедлайны для одной лабы."""
    dates = lab_dates.get(lab_number)
    if not dates or not dates[0]:
        return LabVisibilityInfo(lab_number=lab_number, is_visible=False)

    visible_from, deadline_active_from = dates
    is_visible = visible_from <= today

    if not is_visible:
        return LabVisibilityInfo(
            lab_number=lab_number,
            is_visible=False,
            visible_from=visible_from,
            deadline_active_from=deadline_active_from
        )

    # Уникальные лабы после первого занятия этой лабы
    labs_after = sum(
        1 for wn, first_date in all_labs_ordered
        if first_date > visible_from and wn != lab_number
    )

    # Дедлайны и продления
    deadline_5, deadline_4 = labs_deadlines.get(lab_number, (None, None))
    current_max_grade = 5

    lab_id = labs_ids.get(lab_number)
    extension_bonus = extensions_map.get(lab_id, 0) if lab_id else 0
    has_extension = extension_bonus > 0

    effective_deadline_5 = (deadline_5 + extension_bonus) if deadline_5 is not None else None
    effective_deadline_4 = (deadline_4 + extension_bonus) if deadline_4 is not None else None

    deadline_5_status, lessons_until_5 = _calculate_deadline_status(
        labs_after, effective_deadline_5, visible_from, today
    )
    if deadline_5_status == 'expired':
        current_max_grade = 4

    if effective_deadline_5 is not None:
        logger.debug(
            f"Lab {lab_number}: labs_after={labs_after}, deadline_5={effective_deadline_5}, "
            f"status={deadline_5_status}, visible_from={visible_from}"
        )

    deadline_4_status, lessons_until_4 = _calculate_deadline_status(
        labs_after, effective_deadline_4, visible_from, today
    )
    if deadline_4_status == 'expired':
        current_max_grade = 3

    return LabVisibilityInfo(
        lab_number=lab_number,
        is_visible=True,
        visible_from=visible_from,
        deadline_active_from=deadline_active_from,
        lessons_since_activation=labs_after,
        deadline_5_status=deadline_5_status,
        deadline_4_status=deadline_4_status,
        lessons_until_deadline_5=lessons_until_5,
        lessons_until_deadline_4=lessons_until_4,
        current_max_grade=current_max_grade,
        has_extension=has_extension,
        extension_bonus=extension_bonus
    )
