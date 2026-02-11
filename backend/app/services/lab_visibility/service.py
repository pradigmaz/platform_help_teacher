"""Основной сервис видимости лаб — координация запросов."""

import logging
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab_deadline_extension import LabDeadlineExtension
from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.services.lab_visibility.models import LabVisibilityInfo
from app.services.lab_visibility.session_checker import is_lab_session_now as _is_lab_session_now
from app.services.lab_visibility.visibility_calculator import (
    _build_subgroup_filter,
    calculate_visibility_for_subject,
)
from app.services.schedule_constants import now_msk, today_msk

logger = logging.getLogger(__name__)


class LabVisibilityService:
    """Сервис расчёта видимости лаб по расписанию."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_batch_visibility_info(
        self,
        lab_numbers: list[int],
        group_id: UUID,
        subgroup: int | None,
        labs_deadlines: dict[int, tuple],  # {lab_number: (deadline_5, deadline_4)}
        labs_subjects: dict[int, UUID | None] | None = None,
        labs_ids: dict[int, UUID] | None = None,
    ) -> dict[int, LabVisibilityInfo]:
        """
        Batch-загрузка информации о видимости для нескольких лаб.
        Решает проблему N+1 запросов.

        labs_subjects: словарь {lab_number: subject_id} для фильтрации по предметам.
        labs_ids: словарь {lab_number: lab_id} для проверки продлений дедлайнов.
        """
        if not lab_numbers:
            return {}

        today = today_msk()
        now = now_msk()
        labs_subjects = labs_subjects or {}
        labs_ids = labs_ids or {}

        # Загружаем активные продления для группы
        extensions_map = await self._load_extensions(labs_ids, group_id, now)

        # Группируем лабы по subject_id
        by_subject: dict[UUID | None, list[int]] = {}
        for lab_number in lab_numbers:
            subject_id = labs_subjects.get(lab_number)
            if subject_id not in by_subject:
                by_subject[subject_id] = []
            by_subject[subject_id].append(lab_number)

        result: dict[int, LabVisibilityInfo] = {}

        for subject_id, subject_lab_numbers in by_subject.items():
            subject_result = await calculate_visibility_for_subject(
                db=self.db,
                lab_numbers=subject_lab_numbers,
                group_id=group_id,
                subgroup=subgroup,
                labs_deadlines=labs_deadlines,
                subject_id=subject_id,
                today=today,
                labs_ids=labs_ids,
                extensions_map=extensions_map,
            )
            result.update(subject_result)

        return result

    async def _load_extensions(self, labs_ids: dict[int, UUID], group_id: UUID, now) -> dict[UUID, int]:
        """Загрузить активные продления дедлайнов для группы."""
        if not labs_ids:
            return {}

        lab_id_list = list(labs_ids.values())
        ext_query = select(LabDeadlineExtension).where(
            and_(
                LabDeadlineExtension.lab_id.in_(lab_id_list),
                LabDeadlineExtension.group_id == group_id,
                LabDeadlineExtension.is_active,
                (LabDeadlineExtension.expires_at.is_(None)) | (LabDeadlineExtension.expires_at > now),
            )
        )
        ext_result = await self.db.execute(ext_query)
        return {ext.lab_id: ext.bonus_lessons for ext in ext_result.scalars().all()}

    async def get_visibility_info(
        self,
        lab_number: int,
        group_id: UUID,
        subgroup: int | None,
        deadline_5_lessons: int | None,
        deadline_4_lessons: int | None,
        subject_id: UUID | None = None,
    ) -> LabVisibilityInfo:
        """
        Получить информацию о видимости и дедлайнах одной лабы.
        Для batch-операций используйте get_batch_visibility_info.
        """
        result = await self.get_batch_visibility_info(
            lab_numbers=[lab_number],
            group_id=group_id,
            subgroup=subgroup,
            labs_deadlines={lab_number: (deadline_5_lessons, deadline_4_lessons)},
            labs_subjects={lab_number: subject_id},
        )
        return result.get(lab_number, LabVisibilityInfo(lab_number=lab_number, is_visible=False))

    async def get_visible_lab_numbers_by_subject(
        self,
        group_id: UUID,
        subgroup: int | None,
    ) -> dict[UUID | None, list[int]]:
        """Получить словарь {subject_id: [work_numbers]} видимых лаб."""
        today = today_msk()

        base_filter = [
            Lesson.group_id == group_id,
            Lesson.lesson_type == LessonType.LAB,
            Lesson.is_cancelled.is_(False),
            Lesson.work_number.isnot(None),
            Lesson.date <= today,
        ]
        base_filter.extend(_build_subgroup_filter(subgroup))

        query = select(Lesson.subject_id, Lesson.work_number).where(and_(*base_filter)).distinct()

        result = await self.db.execute(query)

        by_subject: dict[UUID | None, list[int]] = {}
        for row in result.all():
            subject_id = row.subject_id
            work_number = row.work_number
            if subject_id not in by_subject:
                by_subject[subject_id] = []
            if work_number not in by_subject[subject_id]:
                by_subject[subject_id].append(work_number)

        return by_subject

    async def get_visible_lab_numbers(
        self, group_id: UUID, subgroup: int | None, subject_id: UUID | None = None
    ) -> list[int]:
        """Получить список номеров лаб, видимых студенту на сегодня."""
        today = today_msk()

        base_filter = [
            Lesson.group_id == group_id,
            Lesson.lesson_type == LessonType.LAB,
            Lesson.is_cancelled.is_(False),
            Lesson.work_number.isnot(None),
            Lesson.date <= today,
        ]
        base_filter.extend(_build_subgroup_filter(subgroup))
        if subject_id:
            base_filter.append(Lesson.subject_id == subject_id)

        query = select(Lesson.work_number).where(and_(*base_filter)).distinct()
        result = await self.db.execute(query)
        return [row[0] for row in result.all()]

    async def is_lab_session_now(self, group_id: UUID, subgroup: int | None, subject_id: UUID | None = None) -> bool:
        """Проверить идёт ли сейчас лабораторное занятие для студента."""
        return await _is_lab_session_now(self.db, group_id, subgroup, subject_id)
