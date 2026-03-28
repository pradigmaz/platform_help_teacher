"""Сервис бизнес-логики для лабораторных работ."""

import logging
import secrets
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import LAB_PUBLIC_CODE_LENGTH, LAB_PUBLIC_CODE_MAX_ATTEMPTS
from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.schemas.lab import LabCreate, LabUpdate

logger = logging.getLogger(__name__)
_ATTACHABLE_LESSON_TYPES = (LessonType.LAB, LessonType.PRACTICE)


class LabService:
    """Сервис бизнес-логики для лабораторных работ."""

    @staticmethod
    def generate_public_code() -> str:
        """Генерировать уникальный код для публичной ссылки."""
        return secrets.token_urlsafe(LAB_PUBLIC_CODE_LENGTH)[:LAB_PUBLIC_CODE_LENGTH]

    async def _sync_subject_from_lesson(self, db: AsyncSession, lesson_id: UUID | None) -> UUID | None:
        """Получить subject_id из занятия для автоматической привязки."""
        if not lesson_id:
            return None
        lesson = await db.get(Lesson, lesson_id)
        return lesson.subject_id if lesson else None

    async def _validate_subject_lesson_consistency(
        self, db: AsyncSession, subject_id: UUID | None, lesson_id: UUID | None
    ) -> None:
        """BUG-9: Проверить что lesson.subject_id совпадает с lab.subject_id."""
        if not subject_id or not lesson_id:
            return
        lesson = await db.get(Lesson, lesson_id)
        if lesson and lesson.subject_id and lesson.subject_id != subject_id:
            raise ValueError(
                f"Несоответствие предмета: lab.subject_id={subject_id}, lesson.subject_id={lesson.subject_id}"
            )

    async def _sync_origin_lesson(self, db: AsyncSession, lab: Lab) -> None:
        """Обновить legacy origin lesson для совместимости read-path'ов."""
        if not lab.subject_id:
            lab.lesson_id = None
            return

        result = await db.execute(
            select(Lesson)
            .where(
                Lesson.work_number == lab.number,
                Lesson.subject_id == lab.subject_id,
                Lesson.lesson_type.in_(_ATTACHABLE_LESSON_TYPES),
                Lesson.is_cancelled.is_(False),
            )
            .order_by(Lesson.date, Lesson.lesson_number)
            .limit(1)
        )
        origin_lesson = result.scalar_one_or_none()
        lab.lesson_id = origin_lesson.id if origin_lesson else None

    async def _sync_attached_lessons_work_number(
        self,
        db: AsyncSession,
        *,
        subject_id: UUID | None,
        old_number: int,
        new_number: int,
    ) -> None:
        """Сохранить связь lab <-> schedule при переименовании номера работы."""
        if not subject_id or old_number == new_number:
            return

        await db.execute(
            update(Lesson)
            .where(
                Lesson.subject_id == subject_id,
                Lesson.work_number == old_number,
                Lesson.lesson_type.in_(_ATTACHABLE_LESSON_TYPES),
            )
            .values(work_number=new_number)
        )

    async def get_by_id(
        self,
        db: AsyncSession,
        lab_id,
    ) -> Lab | None:
        """Получить лабу по ID."""
        result = await db.execute(select(Lab).where(Lab.id == lab_id, Lab.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def get_by_public_code(self, db: AsyncSession, public_code: str) -> Lab | None:
        """Получить лабу по публичному коду."""
        result = await db.execute(
            select(Lab)
            .where(Lab.public_code == public_code)
            .where(Lab.is_published.is_(True))
            .where(Lab.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, lab_in: LabCreate) -> Lab:
        """Создать лабораторную работу."""
        data = lab_in.model_dump()

        # Автоматически подтягиваем subject_id из занятия
        if data.get("lesson_id") and not data.get("subject_id"):
            data["subject_id"] = await self._sync_subject_from_lesson(db, data["lesson_id"])

        # BUG-9: проверяем согласованность subject_id и lesson_id
        await self._validate_subject_lesson_consistency(db, data.get("subject_id"), data.get("lesson_id"))

        lab = Lab(**data)
        db.add(lab)
        await db.commit()
        await db.refresh(lab)
        logger.info(f"Lab {lab.id} created: {lab.title}")
        return lab

    async def update(self, db: AsyncSession, lab: Lab, lab_in: LabUpdate) -> Lab:
        """Обновить лабораторную работу."""
        update_data = lab_in.model_dump(exclude_unset=True)
        old_number = lab.number
        old_subject_id = lab.subject_id

        # Автоматически синхронизируем subject_id при изменении lesson_id
        if "lesson_id" in update_data:
            new_lesson_id = update_data["lesson_id"]
            if new_lesson_id:
                subject_id = await self._sync_subject_from_lesson(db, new_lesson_id)
                if subject_id:
                    update_data["subject_id"] = subject_id

        # BUG-9: проверяем согласованность subject_id и lesson_id
        final_subject_id = update_data.get("subject_id", lab.subject_id)
        final_lesson_id = update_data.get("lesson_id", lab.lesson_id)
        await self._validate_subject_lesson_consistency(db, final_subject_id, final_lesson_id)

        for field, value in update_data.items():
            setattr(lab, field, value)

        await self._sync_attached_lessons_work_number(
            db,
            subject_id=old_subject_id,
            old_number=old_number,
            new_number=lab.number,
        )

        if lab.number != old_number or lab.subject_id != old_subject_id:
            await self._sync_origin_lesson(db, lab)

        await db.commit()
        await db.refresh(lab)
        logger.info(f"Lab {lab.id} updated")
        return lab

    async def publish(self, db: AsyncSession, lab: Lab) -> str:
        """Опубликовать лабу и вернуть публичный код."""
        if lab.public_code:
            lab.is_published = True
            await db.commit()
            return lab.public_code

        for _ in range(LAB_PUBLIC_CODE_MAX_ATTEMPTS):
            code = self.generate_public_code()
            existing = await self.get_by_public_code(db, code)
            if not existing:
                lab.public_code = code
                lab.is_published = True
                await db.commit()
                await db.refresh(lab)
                logger.info(f"Lab {lab.id} published with code {code}")
                return code

        logger.error(f"Failed to generate unique public_code for lab {lab.id}")
        raise ValueError("Failed to generate unique public code")

    async def unpublish(self, db: AsyncSession, lab: Lab) -> None:
        """Снять лабу с публикации."""
        lab.public_code = None
        lab.is_published = False
        await db.commit()
        await db.refresh(lab)
        logger.info(f"Lab {lab.id} unpublished")

    async def soft_delete(self, db: AsyncSession, lab: Lab) -> None:
        """Мягкое удаление лабы (submissions сохраняются)."""
        lab.deleted_at = datetime.now(UTC)
        lab.is_published = False
        lab.public_code = None
        await db.commit()
        logger.info(f"Lab {lab.id} soft-deleted")

    async def restore(self, db: AsyncSession, lab: Lab) -> None:
        """Восстановить удалённую лабу."""
        lab.deleted_at = None
        await db.commit()
        logger.info(f"Lab {lab.id} restored")


lab_service = LabService()
