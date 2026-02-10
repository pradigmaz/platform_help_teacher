"""
Валидатор привязки лабораторных работ к расписанию.

Правила:
- Нельзя привязать лабу N+1 пока лаба N ещё "активна"
- Лаба активна пока не прошло deadline_5_lessons пар после первого занятия
- Если deadline_5_lessons = None — лаба не блокирует следующую
"""

import logging
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.services.schedule_constants import today_msk

logger = logging.getLogger(__name__)


@dataclass
class AttachmentValidationResult:
    """Результат валидации привязки лабы."""

    is_valid: bool
    blocking_lab_number: int | None = None
    can_attach_from: date | None = None
    message: str = ""


class LabAttachmentValidator:
    """Валидатор привязки лаб к расписанию."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_attachment(
        self, lab_to_attach: Lab, target_lesson_date: date, group_id: UUID, subject_id: UUID | None
    ) -> AttachmentValidationResult:
        """
        Проверить можно ли привязать лабу к занятию.

        Args:
            lab_to_attach: Лаба которую хотим привязать
            target_lesson_date: Дата занятия к которому привязываем
            group_id: ID группы
            subject_id: ID предмета

        Returns:
            AttachmentValidationResult с информацией о валидности
        """
        # Первую лабу всегда можно привязать
        if lab_to_attach.number <= 1:
            return AttachmentValidationResult(is_valid=True)

        prev_lab_number = lab_to_attach.number - 1

        # Получаем предыдущую лабу
        prev_lab = await self._get_lab_by_number(prev_lab_number, subject_id)
        if not prev_lab:
            # Предыдущая лаба не существует — можно привязать
            return AttachmentValidationResult(is_valid=True)

        # Если у предыдущей лабы нет дедлайна — она не блокирует
        if prev_lab.deadline_5_lessons is None:
            return AttachmentValidationResult(is_valid=True)

        # Получаем занятия с предыдущей лабой
        prev_lab_lessons = await self._get_lessons_with_work_number(group_id, subject_id, prev_lab_number)

        if not prev_lab_lessons:
            # Предыдущая лаба не привязана — можно привязать текущую
            return AttachmentValidationResult(is_valid=True)

        # Находим первое занятие с предыдущей лабой
        first_lesson_date = min(lesson.date for lesson in prev_lab_lessons)

        # Считаем уникальные work_number начиная с первого занятия (включительно)
        # deadline_5_lessons = сколько пар (включая первую) можно сдавать на 5
        # Привязка N+1 возможна начиная с пары номер deadline_5_lessons
        unique_labs_count = await self._count_unique_labs_from(first_lesson_date, group_id, subject_id)

        # Можно привязать когда прошло >= deadline_5_lessons уникальных пар
        if unique_labs_count < prev_lab.deadline_5_lessons:
            # Лаба ещё активна
            can_attach_from = await self._get_attachment_available_date(
                first_lesson_date, prev_lab.deadline_5_lessons, group_id, subject_id
            )

            return AttachmentValidationResult(
                is_valid=False,
                blocking_lab_number=prev_lab_number,
                can_attach_from=can_attach_from,
                message=f"Лаба {prev_lab_number} ещё активна. "
                f"Можно привязать лабу {lab_to_attach.number} "
                f"после {can_attach_from.isoformat() if can_attach_from else 'неизвестно'}",
            )

        return AttachmentValidationResult(is_valid=True)

    async def _get_lab_by_number(self, number: int, subject_id: UUID | None) -> Lab | None:
        """Получить лабу по номеру и предмету."""
        query = select(Lab).where(Lab.number == number)
        if subject_id:
            query = query.where(Lab.subject_id == subject_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_lessons_with_work_number(
        self, group_id: UUID, subject_id: UUID | None, work_number: int
    ) -> list[Lesson]:
        """Получить занятия с указанным work_number."""
        filters = [
            Lesson.group_id == group_id,
            Lesson.lesson_type == LessonType.LAB,
            Lesson.work_number == work_number,
            not Lesson.is_cancelled,
        ]
        if subject_id:
            filters.append(Lesson.subject_id == subject_id)

        query = select(Lesson).where(and_(*filters))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _count_unique_labs_from(self, from_date: date, group_id: UUID, subject_id: UUID | None) -> int:
        """
        Посчитать уникальные work_number начиная с указанной даты (включительно).
        Считает только прошедшие занятия (date <= today).
        """
        today = today_msk()

        filters = [
            Lesson.group_id == group_id,
            Lesson.lesson_type == LessonType.LAB,
            Lesson.date >= from_date,
            Lesson.date <= today,
            Lesson.work_number is not None,
            not Lesson.is_cancelled,
        ]
        if subject_id:
            filters.append(Lesson.subject_id == subject_id)

        query = select(func.count(func.distinct(Lesson.work_number))).where(and_(*filters))
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _get_attachment_available_date(
        self, first_lesson_date: date, deadline_5_lessons: int, group_id: UUID, subject_id: UUID | None
    ) -> date | None:
        """
        Получить дату когда можно привязать следующую лабу.

        Это дата N-го уникального занятия начиная с first_lesson_date,
        где N = deadline_5_lessons.
        """
        filters = [
            Lesson.group_id == group_id,
            Lesson.lesson_type == LessonType.LAB,
            Lesson.date >= first_lesson_date,
            Lesson.work_number is not None,
            not Lesson.is_cancelled,
        ]
        if subject_id:
            filters.append(Lesson.subject_id == subject_id)

        # Получаем все занятия начиная с first_lesson_date
        query = select(Lesson.date, Lesson.work_number).where(and_(*filters)).order_by(Lesson.date)
        result = await self.db.execute(query)
        lessons = result.all()

        # Считаем уникальные work_number
        seen_work_numbers = set()
        for lesson_date, work_number in lessons:
            if work_number not in seen_work_numbers:
                seen_work_numbers.add(work_number)
                if len(seen_work_numbers) >= deadline_5_lessons:
                    return lesson_date

        # Не хватает занятий в расписании
        return None
