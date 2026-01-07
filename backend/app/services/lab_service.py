"""Сервис бизнес-логики для лабораторных работ."""
import secrets
import logging
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab import Lab
from app.schemas.lab import LabCreate, LabUpdate
from app.core.constants import LAB_PUBLIC_CODE_LENGTH, LAB_PUBLIC_CODE_MAX_ATTEMPTS

logger = logging.getLogger(__name__)


class LabService:
    """Сервис бизнес-логики для лабораторных работ."""

    @staticmethod
    def generate_public_code() -> str:
        """Генерировать уникальный код для публичной ссылки."""
        return secrets.token_urlsafe(LAB_PUBLIC_CODE_LENGTH)[:LAB_PUBLIC_CODE_LENGTH]

    async def get_by_id(
        self,
        db: AsyncSession,
        lab_id,
    ) -> Optional[Lab]:
        """Получить лабу по ID."""
        result = await db.execute(
            select(Lab).where(Lab.id == lab_id, Lab.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_public_code(
        self,
        db: AsyncSession,
        public_code: str
    ) -> Optional[Lab]:
        """Получить лабу по публичному коду."""
        result = await db.execute(
            select(Lab)
            .where(Lab.public_code == public_code)
            .where(Lab.is_published.is_(True))
            .where(Lab.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        lab_in: LabCreate
    ) -> Lab:
        """Создать лабораторную работу."""
        lab = Lab(**lab_in.model_dump())
        db.add(lab)
        await db.commit()
        await db.refresh(lab)
        logger.info(f"Lab {lab.id} created: {lab.title}")
        return lab

    async def update(
        self,
        db: AsyncSession,
        lab: Lab,
        lab_in: LabUpdate
    ) -> Lab:
        """Обновить лабораторную работу."""
        update_data = lab_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lab, field, value)
        await db.commit()
        await db.refresh(lab)
        logger.info(f"Lab {lab.id} updated")
        return lab

    async def publish(
        self,
        db: AsyncSession,
        lab: Lab
    ) -> str:
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

    async def unpublish(
        self,
        db: AsyncSession,
        lab: Lab
    ) -> None:
        """Снять лабу с публикации."""
        lab.public_code = None
        lab.is_published = False
        await db.commit()
        await db.refresh(lab)
        logger.info(f"Lab {lab.id} unpublished")

    async def soft_delete(
        self,
        db: AsyncSession,
        lab: Lab
    ) -> None:
        """Мягкое удаление лабы (submissions сохраняются)."""
        lab.deleted_at = datetime.now(timezone.utc)
        lab.is_published = False
        lab.public_code = None
        await db.commit()
        logger.info(f"Lab {lab.id} soft-deleted")

    async def restore(
        self,
        db: AsyncSession,
        lab: Lab
    ) -> None:
        """Восстановить удалённую лабу."""
        lab.deleted_at = None
        await db.commit()
        logger.info(f"Lab {lab.id} restored")


lab_service = LabService()
