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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab import Lab
from app.models.lesson import Lesson
from app.services.deadline_lesson_loader import load_ordered_deadline_lessons, load_origin_lessons

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

        origin_lesson = await self._get_origin_lesson(group_id, subject_id, prev_lab_number)
        if not origin_lesson:
            # Предыдущая лаба не привязана — можно привязать текущую
            return AttachmentValidationResult(is_valid=True)

        slot_count = await self._count_deadline_slots_from(origin_lesson.date, target_lesson_date, group_id, subject_id)

        # Можно привязать когда прошло >= deadline_5_lessons уникальных пар
        if slot_count < prev_lab.deadline_5_lessons:
            # Лаба ещё активна
            can_attach_from = await self._get_attachment_available_date(
                origin_lesson.date, prev_lab.deadline_5_lessons, group_id, subject_id
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
        query = select(Lab).where(Lab.number == number, Lab.deleted_at.is_(None))
        if subject_id:
            query = query.where(Lab.subject_id == subject_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_origin_lesson(self, group_id: UUID, subject_id: UUID | None, work_number: int) -> Lesson | None:
        """Получить origin lesson для указанного номера лабы в текущей группе/предмете."""
        return (
            await load_origin_lessons(
                self.db,
                group_id=group_id,
                subject_id=subject_id,
                work_numbers={work_number},
            )
        ).get(work_number)

    async def _count_deadline_slots_from(
        self,
        from_date: date,
        until_date: date,
        group_id: UUID,
        subject_id: UUID | None,
    ) -> int:
        """
        Посчитать deadline slots начиная с origin lesson даты и до target slot включительно.
        Использует ту же ordered slot-sequence, что и student/teacher deadline paths.
        """
        lessons = await load_ordered_deadline_lessons(
            self.db,
            group_id=group_id,
            subject_id=subject_id,
            since_date=from_date,
            until_date=until_date,
        )
        return len(lessons)

    async def _get_attachment_available_date(
        self, first_lesson_date: date, deadline_5_lessons: int, group_id: UUID, subject_id: UUID | None
    ) -> date | None:
        """
        Получить дату когда можно привязать следующую лабу.

        Это дата N-го уникального занятия начиная с first_lesson_date,
        где N = deadline_5_lessons.
        """
        lessons = await load_ordered_deadline_lessons(
            self.db,
            group_id=group_id,
            subject_id=subject_id,
            since_date=first_lesson_date,
        )
        if len(lessons) < deadline_5_lessons:
            return None
        return lessons[deadline_5_lessons - 1][2]
