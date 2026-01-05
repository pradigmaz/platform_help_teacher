"""CRUD операции для модели WorkSubmission."""
import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.work_submission import WorkSubmission
from app.models.work_type import WorkType
from app.models.work import Work

logger = logging.getLogger(__name__)


class CRUDWorkSubmission:
    async def create(
        self,
        db: AsyncSession,
        *,
        work_id: UUID,
        user_id: UUID,
        grade: Optional[int] = None,
        feedback: Optional[str] = None,
        s3_key: Optional[str] = None,
        is_manual: bool = False
    ) -> WorkSubmission:
        db_obj = WorkSubmission(
            work_id=work_id,
            user_id=user_id,
            grade=grade,
            feedback=feedback,
            s3_key=s3_key,
            is_manual=is_manual
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        logger.info(f"Created work submission: {db_obj.id}")
        return db_obj

    async def get(self, db: AsyncSession, id: UUID) -> Optional[WorkSubmission]:
        result = await db.execute(
            select(WorkSubmission).where(WorkSubmission.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_student(
        self,
        db: AsyncSession,
        user_id: UUID,
        work_type: Optional[WorkType] = None
    ) -> List[WorkSubmission]:
        query = select(WorkSubmission).where(WorkSubmission.user_id == user_id)
        
        if work_type:
            query = query.join(Work).where(Work.work_type == work_type)
        
        query = query.order_by(WorkSubmission.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_work(
        self,
        db: AsyncSession,
        work_id: UUID
    ) -> List[WorkSubmission]:
        query = (
            select(WorkSubmission)
            .where(WorkSubmission.work_id == work_id)
            .order_by(WorkSubmission.created_at.desc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_student_and_work(
        self,
        db: AsyncSession,
        user_id: UUID,
        work_id: UUID
    ) -> Optional[WorkSubmission]:
        result = await db.execute(
            select(WorkSubmission).where(
                WorkSubmission.user_id == user_id,
                WorkSubmission.work_id == work_id
            )
        )
        return result.scalar_one_or_none()

    async def update_grade(
        self,
        db: AsyncSession,
        *,
        db_obj: WorkSubmission,
        grade: int,
        feedback: Optional[str] = None
    ) -> WorkSubmission:
        db_obj.grade = grade
        if feedback is not None:
            db_obj.feedback = feedback
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: UUID) -> bool:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            logger.info(f"Deleted work submission: {id}")
            return True
        return False


work_submission = CRUDWorkSubmission()
