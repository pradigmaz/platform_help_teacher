"""
Batch-версии валидаторов слотов для оптимизации bulk-операций.
Загружает данные для всех студентов одним запросом.
"""
import logging
from typing import Dict, Set, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.lesson_grade import LessonGrade
from app.models.attendance import Attendance, AttendanceStatus
from app.models.schedule import LessonType

logger = logging.getLogger(__name__)


async def get_grades_count_on_lesson_batch(
    db: AsyncSession,
    student_ids: List[UUID],
    lesson_id: UUID
) -> Dict[UUID, int]:
    """
    Количество оценок за лабы для списка студентов на занятии.
    Один запрос вместо N.
    """
    query = (
        select(
            LessonGrade.student_id,
            func.count().label('count')
        )
        .where(and_(
            LessonGrade.lesson_id == lesson_id,
            LessonGrade.student_id.in_(student_ids),
            LessonGrade.grade.isnot(None)
        ))
        .group_by(LessonGrade.student_id)
    )
    result = await db.execute(query)
    counts = {row[0]: row[1] for row in result.fetchall()}
    
    # Заполняем нулями тех, у кого нет оценок
    return {sid: counts.get(sid, 0) for sid in student_ids}


async def get_max_labs_per_lesson_batch(
    db: AsyncSession,
    student_ids: List[UUID],
    subject_id: UUID
) -> Dict[UUID, int]:
    """
    Максимум лаб за занятие для списка студентов.
    1 — обычно, 2 — если есть несданные EXCUSED-лабы.
    """
    if not student_ids:
        return {}
    
    # 1. Находим все LAB-занятия с EXCUSED для этих студентов
    excused_query = (
        select(
            Attendance.student_id,
            Lesson.id.label('lesson_id')
        )
        .join(Lesson, Attendance.lesson_id == Lesson.id)
        .where(and_(
            Attendance.student_id.in_(student_ids),
            Attendance.status == AttendanceStatus.EXCUSED,
            Lesson.subject_id == subject_id,
            Lesson.lesson_type == LessonType.LAB,
            Lesson.is_cancelled == False
        ))
    )
    result = await db.execute(excused_query)
    
    # student_id -> set of excused lesson_ids
    excused_lessons: Dict[UUID, Set[UUID]] = {sid: set() for sid in student_ids}
    for row in result.fetchall():
        excused_lessons[row[0]].add(row[1])
    
    # Собираем все excused lesson_ids
    all_excused_lesson_ids = set()
    for lessons in excused_lessons.values():
        all_excused_lesson_ids.update(lessons)
    
    if not all_excused_lesson_ids:
        return {sid: 1 for sid in student_ids}
    
    # 2. Находим лабы привязанные к этим занятиям
    labs_query = (
        select(Lab.lesson_id, Lab.number)
        .where(and_(
            Lab.lesson_id.in_(all_excused_lesson_ids),
            Lab.deleted_at.is_(None)
        ))
    )
    result = await db.execute(labs_query)
    
    # lesson_id -> lab_number
    lesson_to_lab_number: Dict[UUID, int] = {}
    for row in result.fetchall():
        lesson_to_lab_number[row[0]] = row[1]
    
    # student_id -> set of excused lab numbers
    excused_lab_numbers: Dict[UUID, Set[int]] = {sid: set() for sid in student_ids}
    for sid, lesson_ids in excused_lessons.items():
        for lid in lesson_ids:
            if lid in lesson_to_lab_number:
                excused_lab_numbers[sid].add(lesson_to_lab_number[lid])
    
    # Собираем все номера лаб для проверки сданных
    all_lab_numbers = set()
    for numbers in excused_lab_numbers.values():
        all_lab_numbers.update(numbers)
    
    if not all_lab_numbers:
        return {sid: 1 for sid in student_ids}
    
    # 3. Считаем сданные лабы по этим номерам
    grades_query = (
        select(
            LessonGrade.student_id,
            LessonGrade.work_number
        )
        .join(Lesson, LessonGrade.lesson_id == Lesson.id)
        .where(and_(
            LessonGrade.student_id.in_(student_ids),
            Lesson.subject_id == subject_id,
            LessonGrade.work_number.in_(all_lab_numbers),
            LessonGrade.grade.isnot(None)
        ))
        .distinct()
    )
    result = await db.execute(grades_query)
    
    # student_id -> set of submitted lab numbers
    submitted: Dict[UUID, Set[int]] = {sid: set() for sid in student_ids}
    for row in result.fetchall():
        submitted[row[0]].add(row[1])
    
    # 4. Вычисляем max_labs для каждого студента
    result_dict: Dict[UUID, int] = {}
    for sid in student_ids:
        excused_nums = excused_lab_numbers.get(sid, set())
        submitted_nums = submitted.get(sid, set())
        unsubmitted_count = len(excused_nums - submitted_nums)
        result_dict[sid] = 2 if unsubmitted_count > 0 else 1
    
    return result_dict
