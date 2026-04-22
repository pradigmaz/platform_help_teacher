"""
Batch-версия валидатора дедлайнов для оптимизации bulk-операций.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance, AttendanceStatus
from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.services.deadline_context import (
    build_deadline_context_for_current_lesson,
    resolve_last_work_number_index,
)
from app.services.deadline_engine import evaluate_deadline_context
from app.services.deadline_inputs import load_active_extension_bonus_map
from app.services.deadline_lesson_loader import load_ordered_deadline_lessons, load_origin_lessons
from app.services.lab_lookup import find_active_labs_by_subject_and_numbers

logger = logging.getLogger(__name__)
_DEADLINE_LESSON_TYPES = (LessonType.LAB, LessonType.PRACTICE)


async def _get_origin_lessons_for_group(
    db: AsyncSession,
    current_lesson: Lesson,
    work_numbers: set[int],
) -> dict[int, Lesson]:
    """Resolve first lesson slot per work_number in current lesson's group/subject."""
    return await load_origin_lessons(
        db,
        group_id=current_lesson.group_id,
        subject_id=current_lesson.subject_id,
        work_numbers=work_numbers,
        subgroup=current_lesson.subgroup,
    )


async def get_max_allowed_grades_batch(
    db: AsyncSession,
    lesson: Lesson,
    grade_items: list[tuple[UUID, int | None]],  # [(student_id, work_number), ...]
) -> dict[tuple[UUID, int | None], int]:
    """
    Batch-версия get_max_allowed_grade.

    Args:
        lesson: Занятие на котором ставятся оценки
        grade_items: Список (student_id, work_number)

    Returns:
        Dict: {(student_id, work_number): max_grade}
    """
    if lesson.lesson_type not in _DEADLINE_LESSON_TYPES:
        return {item: 5 for item in grade_items}

    # Собираем уникальные work_numbers
    work_numbers = set()
    for _, wn in grade_items:
        if wn:
            work_numbers.add(wn)
        elif lesson.work_number:
            work_numbers.add(lesson.work_number)

    if not work_numbers:
        return {item: 5 for item in grade_items}

    # 1. Загружаем все нужные лабы одним запросом
    labs = await find_active_labs_by_subject_and_numbers(db, lesson.subject_id, work_numbers)

    if not labs:
        return {item: 5 for item in grade_items}

    extension_bonus_by_lab_id = await load_active_extension_bonus_map(
        db,
        lab_ids={lab.id for lab in labs.values()},
        group_id=lesson.group_id,
        now=datetime.now(UTC),
    )

    # 2. Находим origin lessons в текущей группе, а не по глобальному lab.lesson_id.
    origin_lessons_by_number = await _get_origin_lessons_for_group(db, lesson, work_numbers)
    origin_lesson_ids = {origin.id for origin in origin_lessons_by_number.values()}
    student_ids = {sid for sid, _ in grade_items}

    # 3. Загружаем EXCUSED статусы одним запросом
    excused_pairs: set[tuple[UUID, UUID]] = set()  # (student_id, lesson_id)
    if origin_lesson_ids and student_ids:
        excused_query = select(Attendance.student_id, Attendance.lesson_id).where(
            and_(
                Attendance.lesson_id.in_(origin_lesson_ids),
                Attendance.student_id.in_(student_ids),
                Attendance.status == AttendanceStatus.EXCUSED,
            )
        )
        result = await db.execute(excused_query)
        excused_pairs = {(row[0], row[1]) for row in result.fetchall()}

    # 4. Карта origin lessons по id для расчёта индексов.
    origin_lessons = {origin.id: origin for origin in origin_lessons_by_number.values()}

    # 5. Загружаем все lab/practice-занятия для расчёта индексов (один запрос)
    # Находим минимальную дату среди origin_lessons
    if origin_lessons:
        min_date = min(ol.date for ol in origin_lessons.values())
        all_lessons = await load_ordered_deadline_lessons(
            db,
            group_id=lesson.group_id,
            subject_id=lesson.subject_id,
            subgroup=lesson.subgroup,
            since_date=min_date,
        )
    else:
        all_lessons = []

    # Строим индекс: lesson_id -> position
    lesson_positions = {lid: idx for idx, (lid, _, _, _) in enumerate(all_lessons)}
    activation_lesson_ids = {
        lab_number: all_lessons[activation_index][0]
        for lab_number in labs
        if (
            activation_index := resolve_last_work_number_index(
                [work_number for _, work_number, _, _ in all_lessons],
                lab_number,
            )
        )
        is not None
    }
    # 6. Вычисляем max_grade для каждого item
    results: dict[tuple[UUID, int | None], int] = {}

    for student_id, work_number in grade_items:
        lab_num = work_number or lesson.work_number
        if not lab_num or lab_num not in labs:
            results[(student_id, work_number)] = 5
            continue

        lab = labs[lab_num]
        origin_lesson = origin_lessons_by_number.get(lab_num)

        # Проверяем EXCUSED
        if origin_lesson and (student_id, origin_lesson.id) in excused_pairs:
            results[(student_id, work_number)] = 5
            continue

        # Нет дедлайнов
        if lab.deadline_5_lessons is None and lab.deadline_4_lessons is None:
            results[(student_id, work_number)] = 5
            continue

        # Вычисляем индекс
        if origin_lesson is None or origin_lesson.id not in origin_lessons:
            results[(student_id, work_number)] = 5
            continue

        context = build_deadline_context_for_current_lesson(
            lab_number=lab_num,
            origin_lesson_id=activation_lesson_ids.get(lab_num, origin_lesson.id),
            current_lesson_id=lesson.id,
            lesson_positions=lesson_positions,
            extension_bonus=extension_bonus_by_lab_id.get(lab.id, 0),
        )
        if context.lesson_index is None:
            results[(student_id, work_number)] = 5
            continue

        evaluation = evaluate_deadline_context(
            context=context,
            deadline_5_lessons=lab.deadline_5_lessons,
            deadline_4_lessons=lab.deadline_4_lessons,
        )
        results[(student_id, work_number)] = evaluation.state.current_max_grade

    return results
