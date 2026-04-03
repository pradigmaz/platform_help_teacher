"""CRUD операции для объявлений."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.announcement import Announcement


class CRUDAnnouncement:
    async def get(self, db: AsyncSession, announcement_id: UUID) -> Announcement | None:
        """Получить объявление по ID."""
        result = await db.execute(
            select(Announcement).options(selectinload(Announcement.author)).where(Announcement.id == announcement_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, db: AsyncSession, skip: int = 0, limit: int = 100, include_drafts: bool = True
    ) -> list[Announcement]:
        """Получить все объявления (для админа)."""
        query = select(Announcement).options(selectinload(Announcement.author))
        if not include_drafts:
            query = query.where(Announcement.is_draft.is_(False))
        query = query.order_by(Announcement.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_published(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Announcement]:
        """Получить опубликованные объявления (для студентов)."""
        result = await db.execute(
            select(Announcement)
            .where(Announcement.is_draft.is_(False))
            .order_by(Announcement.published_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, title: str, content: str, created_by: UUID) -> Announcement:
        """Создать черновик объявления."""
        announcement = Announcement(title=title, content=content, created_by=created_by, is_draft=True)
        db.add(announcement)
        await db.commit()
        await db.refresh(announcement)
        return announcement

    async def update(
        self, db: AsyncSession, announcement: Announcement, title: str | None = None, content: str | None = None
    ) -> Announcement:
        """Обновить объявление."""
        if title is not None:
            announcement.title = title
        if content is not None:
            announcement.content = content
        await db.commit()
        await db.refresh(announcement)
        return announcement

    async def publish(self, db: AsyncSession, announcement: Announcement) -> Announcement:
        """Опубликовать объявление."""
        announcement.is_draft = False
        announcement.published_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(announcement)
        return announcement

    async def delete(self, db: AsyncSession, announcement_id: UUID) -> bool:
        """Удалить объявление."""
        announcement = await self.get(db, announcement_id)
        if announcement:
            await db.delete(announcement)
            await db.commit()
            return True
        return False


crud_announcement = CRUDAnnouncement()
