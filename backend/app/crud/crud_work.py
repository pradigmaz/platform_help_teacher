"""CRUD операции для модели Work."""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.work import Work
from app.models.work_type import WorkType

logger = logging.getLogger(__name__)


class CRUDWork:
    async def create(
        self,
        db: AsyncSession,
        *,
        title: str,
        work_type: WorkType,
        max_grade: int = 10,
        description: str | None = None,
        deadline: str | None = None,
        s3_key: str | None = None
    ) -> Work:
        db_obj = Work(
            title=title,
            work_type=work_type,
            max_grade=max_grade,
            description=description,
            deadline=deadline,
            s3_key=s3_key
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        logger.info(f"Created work: {db_obj.id} ({work_type})")
        return db_obj

    async def get(self, db: AsyncSession, id: UUID) -> Work | None:
        result = await db.execute(select(Work).where(Work.id == id))
        return result.scalar_one_or_none()

    async def get_by_type(
        self,
        db: AsyncSession,
        work_type: WorkType,
        limit: int = 100,
        offset: int = 0
    ) -> list[Work]:
        query = (
            select(Work)
            .where(Work.work_type == work_type)
            .order_by(Work.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_all(
        self,
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0
    ) -> list[Work]:
        query = (
            select(Work)
            .order_by(Work.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Work,
        title: str | None = None,
        description: str | None = None,
        max_grade: int | None = None,
        deadline: str | None = None,
        s3_key: str | None = None
    ) -> Work:
        if title is not None:
            db_obj.title = title
        if description is not None:
            db_obj.description = description
        if max_grade is not None:
            db_obj.max_grade = max_grade
        if deadline is not None:
            db_obj.deadline = deadline
        if s3_key is not None:
            db_obj.s3_key = s3_key

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: UUID) -> bool:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            logger.info(f"Deleted work: {id}")
            return True
        return False


work = CRUDWork()
