"""Расчёт видимости и дедлайнов лаб по расписанию."""

import logging
from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.services.deadline_context import build_deadline_context_for_visibility
from app.services.deadline_engine import evaluate_deadline_context
from app.services.deadline_lesson_loader import build_deadline_lesson_filter, load_ordered_deadline_lessons
from app.services.deadline_trace import resolve_effective_deadline_date
from app.services.lab_visibility.models import LabVisibilityInfo

logger = logging.getLogger(__name__)


def _build_subgroup_filter(subgroup: int | None) -> list:
    """Backward-compatible subgroup filter helper used by LabVisibilityService."""
    if subgroup is not None:
        return [(Lesson.subgroup.is_(None)) | (Lesson.subgroup == subgroup)]
    return []


async def calculate_visibility_for_subject(
    db: AsyncSession,
    lab_numbers: list[int],
    group_id: UUID,
    subgroup: int | None,
    labs_deadlines: dict[int, tuple],
    subject_id: UUID | None,
    today: date,
    labs_ids: dict[int, UUID] | None = None,
    extensions_map: dict[UUID, int] | None = None,
    excused_lab_numbers: set[int] | None = None,
) -> dict[int, LabVisibilityInfo]:
    """Получить visibility для лаб одного предмета."""
    labs_ids = labs_ids or {}
    extensions_map = extensions_map or {}
    excused_lab_numbers = excused_lab_numbers or set()

    base_filter = build_deadline_lesson_filter(group_id=group_id, subgroup=subgroup, subject_id=subject_id)

    # 1. MIN/MAX даты для всех лаб одним запросом
    dates_query = (
        select(Lesson.work_number, func.min(Lesson.date).label("min_date"), func.max(Lesson.date).label("max_date"))
        .where(and_(*base_filter, Lesson.work_number.in_(lab_numbers)))
        .group_by(Lesson.work_number)
    )

    dates_result = await db.execute(dates_query)
    lab_dates = {row.work_number: (row.min_date, row.max_date) for row in dates_result.all()}

    # 2. Все фактические lab/practice-слоты до today для подсчёта дедлайнов.
    # Важно: сюда входят и слоты без work_number, как в teacher-side validator.
    ordered_lessons = [
        (work_number, lesson_date, lesson_number)
        for _, work_number, lesson_date, lesson_number in await load_ordered_deadline_lessons(
            db,
            group_id=group_id,
            subject_id=subject_id,
            subgroup=subgroup,
            until_date=today,
        )
    ]
    ordered_lessons_for_trace = [
        (work_number, lesson_date)
        for _, work_number, lesson_date, _ in await load_ordered_deadline_lessons(
            db,
            group_id=group_id,
            subject_id=subject_id,
            subgroup=subgroup,
        )
    ]

    # 3. Строим результат для каждой лабы
    result = {}
    for lab_number in lab_numbers:
        result[lab_number] = _calculate_single_lab_visibility(
            lab_number=lab_number,
            lab_dates=lab_dates,
            ordered_lessons=ordered_lessons,
            labs_deadlines=labs_deadlines,
            labs_ids=labs_ids,
            extensions_map=extensions_map,
            excused_lab_numbers=excused_lab_numbers,
            ordered_lessons_for_trace=ordered_lessons_for_trace,
            today=today,
        )

    return result


def _calculate_single_lab_visibility(
    lab_number: int,
    lab_dates: dict[int, tuple[date, date]],
    ordered_lessons: list[tuple[int, date, int]],
    labs_deadlines: dict[int, tuple],
    labs_ids: dict[int, UUID],
    extensions_map: dict[UUID, int],
    excused_lab_numbers: set[int],
    today: date,
    ordered_lessons_for_trace: list[tuple[int | None, date]] | None = None,
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
            deadline_active_from=deadline_active_from,
        )

    # Дедлайны и продления
    deadline_5, deadline_4 = labs_deadlines.get(lab_number, (None, None))
    ordered_lessons_for_trace = ordered_lessons_for_trace or [
        (work_number, lesson_date) for work_number, lesson_date, _ in ordered_lessons
    ]

    lab_id = labs_ids.get(lab_number)
    context = build_deadline_context_for_visibility(
        lab_number=lab_number,
        ordered_lessons=ordered_lessons,
        lab_id=lab_id,
        extensions_map=extensions_map,
        excused_lab_numbers=excused_lab_numbers,
    )
    effective_deadline_5_date = resolve_effective_deadline_date(
        ordered_lessons=ordered_lessons_for_trace,
        lab_number=lab_number,
        effective_deadline_lessons=context.extension_bonus + deadline_5 if deadline_5 is not None else None,
    )
    effective_deadline_4_date = resolve_effective_deadline_date(
        ordered_lessons=ordered_lessons_for_trace,
        lab_number=lab_number,
        effective_deadline_lessons=context.extension_bonus + deadline_4 if deadline_4 is not None else None,
    )
    evaluation = evaluate_deadline_context(
        context=context,
        deadline_5_lessons=deadline_5,
        deadline_4_lessons=deadline_4,
        visible_from=visible_from,
        today=today,
        effective_deadline_5_date=effective_deadline_5_date,
        effective_deadline_4_date=effective_deadline_4_date,
    )

    if deadline_5 is not None:
        logger.debug(
            f"Lab {lab_number}: labs_after={context.lesson_index or 0}, deadline_5={deadline_5 + context.extension_bonus}, "
            f"status={evaluation.state.deadline_5_status}, visible_from={visible_from}"
        )

    return LabVisibilityInfo(
        lab_number=lab_number,
        is_visible=True,
        visible_from=visible_from,
        deadline_active_from=deadline_active_from,
        lessons_since_activation=context.lesson_index or 0,
        deadline_5_status=evaluation.state.deadline_5_status,
        deadline_4_status=evaluation.state.deadline_4_status,
        lessons_until_deadline_5=evaluation.state.lessons_until_deadline_5,
        lessons_until_deadline_4=evaluation.state.lessons_until_deadline_4,
        current_max_grade=evaluation.state.current_max_grade,
        lesson_index=evaluation.state.lesson_index,
        has_extension=evaluation.trace.has_extension,
        extension_bonus=context.extension_bonus,
        is_excused_origin=context.is_excused_origin,
        effective_deadline_5_date=evaluation.trace.effective_deadline_5_date,
        effective_deadline_4_date=evaluation.trace.effective_deadline_4_date,
    )
