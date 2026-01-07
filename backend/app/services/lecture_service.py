"""Сервис бизнес-логики для лекций."""
import secrets
import string
import logging
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lecture import Lecture
from app.core.constants import LECTURE_PUBLIC_CODE_LENGTH, LECTURE_PUBLIC_CODE_MAX_ATTEMPTS

logger = logging.getLogger(__name__)


class LectureService:
    """Сервис бизнес-логики для лекций."""

    @staticmethod
    def generate_public_code() -> str:
        """Генерировать уникальный код для публичной ссылки."""
        alphabet = string.ascii_lowercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(LECTURE_PUBLIC_CODE_LENGTH))

    async def get_by_public_code(
        self,
        db: AsyncSession,
        public_code: str
    ) -> Optional[Lecture]:
        """Получить лекцию по публичному коду."""
        result = await db.execute(
            select(Lecture)
            .options(selectinload(Lecture.images), selectinload(Lecture.subject))
            .where(Lecture.public_code == public_code)
            .where(Lecture.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def publish(
        self,
        db: AsyncSession,
        lecture: Lecture
    ) -> str:
        """Опубликовать лекцию и вернуть публичный код."""
        if lecture.public_code:
            lecture.is_published = True
            await db.commit()
            return lecture.public_code

        for _ in range(LECTURE_PUBLIC_CODE_MAX_ATTEMPTS):
            code = self.generate_public_code()
            existing = await self.get_by_public_code(db, code)
            if not existing:
                lecture.public_code = code
                lecture.is_published = True
                await db.commit()
                await db.refresh(lecture)
                logger.info(f"Lecture {lecture.id} published with code {code}")
                return code

        raise ValueError("Failed to generate unique public code")

    async def unpublish(
        self,
        db: AsyncSession,
        lecture: Lecture
    ) -> None:
        """Снять лекцию с публикации."""
        lecture.public_code = None
        lecture.is_published = False
        await db.commit()
        await db.refresh(lecture)
        logger.info(f"Lecture {lecture.id} unpublished")

    async def soft_delete(
        self,
        db: AsyncSession,
        lecture: Lecture
    ) -> None:
        """Мягкое удаление лекции."""
        lecture.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"Lecture {lecture.id} soft-deleted")

    async def restore(
        self,
        db: AsyncSession,
        lecture: Lecture
    ) -> None:
        """Восстановить удалённую лекцию."""
        lecture.deleted_at = None
        await db.commit()
        logger.info(f"Lecture {lecture.id} restored")


lecture_service = LectureService()
