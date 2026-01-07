"""CRUD операции для лекций."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lecture import Lecture
from app.schemas.lecture import LectureCreate, LectureUpdate


class CRUDLecture:
    """CRUD операции для лекций."""

    async def create(
        self,
        db: AsyncSession,
        data: LectureCreate
    ) -> Lecture:
        """Создать лекцию."""
        lecture = Lecture(
            title=data.title,
            content=data.content,
            subject_id=data.subject_id
        )
        db.add(lecture)
        await db.commit()
        
        # Перезагружаем с eager loading для images и subject
        result = await db.execute(
            select(Lecture)
            .options(selectinload(Lecture.images), selectinload(Lecture.subject))
            .where(Lecture.id == lecture.id)
        )
        return result.scalar_one()

    async def get(
        self,
        db: AsyncSession,
        lecture_id: UUID,
        include_deleted: bool = False
    ) -> Optional[Lecture]:
        """Получить лекцию по ID."""
        query = (
            select(Lecture)
            .options(selectinload(Lecture.images), selectinload(Lecture.subject))
            .where(Lecture.id == lecture_id)
        )
        if not include_deleted:
            query = query.where(Lecture.deleted_at.is_(None))
        result = await db.execute(query)
        return result.scalar_one_or_none()

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


    async def list_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        subject_id: Optional[UUID] = None,
        include_deleted: bool = False
    ) -> List[Lecture]:
        """Получить список всех лекций."""
        query = select(Lecture).options(selectinload(Lecture.subject))
        
        if not include_deleted:
            query = query.where(Lecture.deleted_at.is_(None))
        
        if subject_id:
            query = query.where(Lecture.subject_id == subject_id)
        
        query = query.order_by(Lecture.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        db: AsyncSession,
        lecture: Lecture,
        data: LectureUpdate
    ) -> Lecture:
        """Обновить лекцию."""
        if data.title is not None:
            lecture.title = data.title
        if data.content is not None:
            lecture.content = data.content
        if data.subject_id is not None:
            lecture.subject_id = data.subject_id

        await db.commit()
        
        # Перезагружаем с eager loading для images и subject
        result = await db.execute(
            select(Lecture)
            .options(selectinload(Lecture.images), selectinload(Lecture.subject))
            .where(Lecture.id == lecture.id)
        )
        return result.scalar_one()

    async def delete(
        self,
        db: AsyncSession,
        lecture_id: UUID
    ) -> bool:
        """Жёсткое удаление лекции (для совместимости)."""
        lecture = await self.get(db, lecture_id, include_deleted=True)
        if lecture:
            await db.delete(lecture)
            await db.commit()
            return True
        return False


crud_lecture = CRUDLecture()
