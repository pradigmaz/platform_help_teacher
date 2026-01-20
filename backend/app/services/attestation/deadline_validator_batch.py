"""
Batch-версия валидатора дедлайнов для оптимизации bulk-операций.
"""
import logging
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.attendance import Attendance, AttendanceStatus
from app.models.schedule import LessonType

logger = logging.getLogger(__name__)


async def get_max_allowed_grades_batch(
    db: AsyncSession,
    lesson: Lesson,
    grade_items: List[Tuple[UUID, Optional[int]]]  # [(student_id, work_number), ...]
) -> Dict[Tuple[UUID, Optional[int]], int]:
    """
    Batch-версия get_max_allowed_grade.
    
    Args:
        lesson: Занятие на котором ставятся оценки
        grade_items: Список (student_id, work_number)
    
    Returns:
        Dict: {(student_id, work_number): max_grade}
    """
    if lesson.lesson_type != LessonType.LAB:
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
    labs_query = select(Lab).where(and_(
        Lab.subject_id == lesson.subject_id,
        Lab.number.in_(work_numbers),
        Lab.deleted_at.is_(None)
    ))
    result = await db.execute(labs_query)
    labs = {lab.number: lab for lab in result.scalars().all()}
    
    if not labs:
        return {item: 5 for item in grade_items}
    
    # 2. Собираем lesson_ids для проверки EXCUSED
    origin_lesson_ids = {lab.lesson_id for lab in labs.values() if lab.lesson_id}
    student_ids = {sid for sid, _ in grade_items}
    
    # 3. Загружаем EXCUSED статусы одним запросом
    excused_pairs: set[Tuple[UUID, UUID]] = set()  # (student_id, lesson_id)
    if origin_lesson_ids and student_ids:
        excused_query = select(
            Attendance.student_id,
            Attendance.lesson_id
        ).where(and_(
            Attendance.lesson_id.in_(origin_lesson_ids),
            Attendance.student_id.in_(student_ids),
            Attendance.status == AttendanceStatus.EXCUSED
        ))
        result = await db.execute(excused_query)
        excused_pairs = {(row[0], row[1]) for row in result.fetchall()}
    
    # 4. Загружаем origin_lessons для расчёта индексов
    origin_lessons: Dict[UUID, Lesson] = {}
    if origin_lesson_ids:
        ol_query = select(Lesson).where(Lesson.id.in_(origin_lesson_ids))
        result = await db.execute(ol_query)
        origin_lessons = {ol.id: ol for ol in result.scalars().all()}
    
    # 5. Загружаем все LAB-занятия для расчёта индексов (один запрос)
    # Находим минимальную дату среди origin_lessons
    if origin_lessons:
        min_date = min(ol.date for ol in origin_lessons.values())
        lessons_query = (
            select(Lesson.id, Lesson.date, Lesson.lesson_number)
            .where(and_(
                Lesson.group_id == lesson.group_id,
                Lesson.subject_id == lesson.subject_id,
                Lesson.lesson_type == 'LAB',
                Lesson.is_cancelled == False,
                Lesson.date >= min_date
            ))
            .order_by(Lesson.date, Lesson.lesson_number)
        )
        result = await db.execute(lessons_query)
        all_lessons = list(result.fetchall())
    else:
        all_lessons = []
    
    # Строим индекс: lesson_id -> position
    lesson_positions = {lid: idx for idx, (lid, _, _) in enumerate(all_lessons)}
    current_pos = lesson_positions.get(lesson.id)
    
    # 6. Вычисляем max_grade для каждого item
    results: Dict[Tuple[UUID, Optional[int]], int] = {}
    
    for student_id, work_number in grade_items:
        lab_num = work_number or lesson.work_number
        if not lab_num or lab_num not in labs:
            results[(student_id, work_number)] = 5
            continue
        
        lab = labs[lab_num]
        
        # Проверяем EXCUSED
        if lab.lesson_id and (student_id, lab.lesson_id) in excused_pairs:
            results[(student_id, work_number)] = 5
            continue
        
        # Нет дедлайнов
        if lab.deadline_5_lessons is None and lab.deadline_4_lessons is None:
            results[(student_id, work_number)] = 5
            continue
        
        # Вычисляем индекс
        if not lab.lesson_id or lab.lesson_id not in origin_lessons:
            results[(student_id, work_number)] = 5
            continue
        
        origin_pos = lesson_positions.get(lab.lesson_id)
        if origin_pos is None or current_pos is None:
            results[(student_id, work_number)] = 5
            continue
        
        lesson_index = current_pos - origin_pos
        
        # Проверяем дедлайны
        if lab.deadline_4_lessons is not None and lesson_index > lab.deadline_4_lessons:
            results[(student_id, work_number)] = 3
        elif lab.deadline_5_lessons is not None and lesson_index > lab.deadline_5_lessons:
            results[(student_id, work_number)] = 4
        else:
            results[(student_id, work_number)] = 5
    
    return results
