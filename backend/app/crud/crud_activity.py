from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityUpdate
from app.models.attestation_settings import AttestationType

class CRUDActivity:
    async def create(self, db: AsyncSession, *, obj_in: ActivityCreate, created_by_id: UUID) -> Activity:
        db_obj = Activity(
            student_id=obj_in.student_id,
            points=obj_in.points,
            description=obj_in.description,
            attestation_type=obj_in.attestation_type,
            is_active=obj_in.is_active,
            created_by_id=created_by_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def create_batch(
        self, 
        db: AsyncSession, 
        *, 
        student_ids: List[UUID], 
        points: float, 
        description: str, 
        attestation_type: AttestationType,
        batch_id: UUID,
        created_by_id: UUID
    ) -> List[Activity]:
        activities = []
        for student_id in student_ids:
            activity = Activity(
                student_id=student_id,
                points=points,
                description=description,
                attestation_type=attestation_type,
                batch_id=batch_id,
                created_by_id=created_by_id
            )
            activities.append(activity)
            db.add(activity)
        
        await db.commit()
        return activities

    async def get_by_student(
        self, 
        db: AsyncSession, 
        student_id: UUID, 
        attestation_type: Optional[AttestationType] = None
    ) -> List[Activity]:
        query = select(Activity).where(
            Activity.student_id == student_id,
            Activity.is_active == True
        )
        if attestation_type:
            query = query.where(Activity.attestation_type == attestation_type)
        
        query = query.order_by(Activity.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_all(
        self,
        db: AsyncSession,
        attestation_type: Optional[AttestationType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Activity]:
        """Get all activities with student info, ordered by date desc."""
        query = select(Activity).where(Activity.is_active == True)
        if attestation_type:
            query = query.where(Activity.attestation_type == attestation_type)
        
        query = query.order_by(Activity.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get(self, db: AsyncSession, id: UUID) -> Optional[Activity]:
        result = await db.execute(select(Activity).where(Activity.id == id))
        return result.scalar_one_or_none()

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: Activity, 
        obj_in: ActivityUpdate
    ) -> Activity:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: UUID) -> Optional[Activity]:
        # Soft delete
        db_obj = await self.get(db, id)
        if db_obj:
            db_obj.is_active = False
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
        return db_obj

activity = CRUDActivity()

