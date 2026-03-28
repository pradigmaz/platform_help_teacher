"""Основной сервис видимости лаб — координация запросов."""

import logging
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.services.deadline_inputs import load_active_extension_bonus_map, load_excused_origin_numbers
from app.services.deadline_lesson_loader import load_origin_lessons
from app.services.lab_visibility.models import LabVisibilityInfo
from app.services.lab_visibility.session_checker import (
    get_current_lab_session as _get_current_lab_session,
)
from app.services.lab_visibility.session_checker import (
    is_lab_session_now as _is_lab_session_now,
)
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
        student_id: UUID | None = None,
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
            origin_lessons = await load_origin_lessons(
                self.db,
                group_id=group_id,
                subject_id=subject_id,
                work_numbers=set(subject_lab_numbers),
                subgroup=subgroup,
            )
            excused_lab_numbers = await self._load_excused_lab_numbers(
                student_id=student_id,
                origin_lessons_by_number=origin_lessons,
            )
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
                excused_lab_numbers=excused_lab_numbers,
            )
            result.update(subject_result)

        return result

    async def _load_extensions(self, labs_ids: dict[int, UUID], group_id: UUID, now) -> dict[UUID, int]:
        """Загрузить активные продления дедлайнов для группы."""
        return await load_active_extension_bonus_map(
            self.db,
            lab_ids=set(labs_ids.values()),
            group_id=group_id,
            now=now,
        )

    async def _load_excused_lab_numbers(
        self,
        student_id: UUID | None,
        origin_lessons_by_number: dict[int, Lesson],
    ) -> set[int]:
        """Получить номера лаб, где студент был EXCUSED на origin slot в текущем расписании группы."""
        return await load_excused_origin_numbers(
            self.db,
            student_id=student_id,
            origin_lessons_by_number=origin_lessons_by_number,
        )

    async def get_visibility_info(
        self,
        lab_number: int,
        group_id: UUID,
        subgroup: int | None,
        deadline_5_lessons: int | None,
        deadline_4_lessons: int | None,
        subject_id: UUID | None = None,
        lab_id: UUID | None = None,
        student_id: UUID | None = None,
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
            labs_ids={lab_number: lab_id} if lab_id else None,
            student_id=student_id,
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
            Lesson.lesson_type.in_((LessonType.LAB, LessonType.PRACTICE)),
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

    async def get_group_subject_ids(self, group_id: UUID, subgroup: int | None) -> set[UUID]:
        """Получить предметы группы из расписания, даже если их пары ещё не начались."""
        base_filter = [
            Lesson.group_id == group_id,
            Lesson.lesson_type.in_((LessonType.LAB, LessonType.PRACTICE)),
            Lesson.is_cancelled.is_(False),
            Lesson.subject_id.isnot(None),
        ]
        base_filter.extend(_build_subgroup_filter(subgroup))

        query = select(Lesson.subject_id).where(and_(*base_filter)).distinct()
        result = await self.db.execute(query)
        return {row[0] for row in result.all() if row[0] is not None}

    async def get_visible_lab_numbers(
        self, group_id: UUID, subgroup: int | None, subject_id: UUID | None = None
    ) -> list[int]:
        """Получить список номеров лаб, видимых студенту на сегодня."""
        today = today_msk()

        base_filter = [
            Lesson.group_id == group_id,
            Lesson.lesson_type.in_((LessonType.LAB, LessonType.PRACTICE)),
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

    async def get_current_lab_session(
        self, group_id: UUID, subgroup: int | None, subject_id: UUID | None = None
    ) -> Lesson | None:
        """Получить текущее lab/practice-занятие для студента."""
        return await _get_current_lab_session(self.db, group_id, subgroup, subject_id)
