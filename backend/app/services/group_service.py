import secrets
import logging
from uuid import UUID
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from app import models, schemas

logger = logging.getLogger(__name__)

class GroupService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def generate_invite_code(self, length: int = 8) -> str:
        """Генерация уникального инвайт-кода"""
        chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
        return ''.join(secrets.choice(chars) for _ in range(length))

    async def create_with_students(self, group_in: schemas.GroupCreate) -> models.Group:
        """Создать новую группу с настройками и студентами."""
        # Check if group exists
        result = await self.db.execute(select(models.Group).where(models.Group.code == group_in.code))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Group with this code already exists")

        try:
            group = models.Group(
                name=group_in.name,
                code=group_in.code,
                labs_count=group_in.labs_count,
                grading_scale=group_in.grading_scale,
                default_max_grade=group_in.default_max_grade,
            )
            self.db.add(group)
            await self.db.flush()

            if group_in.students:
                # Валидация количества студентов при создании
                if len(group_in.students) > 150:
                     raise HTTPException(status_code=400, detail="Too many students in one request (max 150)")

                # Batch generate codes
                invite_codes = await self._generate_unique_invite_codes_batch(len(group_in.students))

                for i, student_data in enumerate(group_in.students):
                    new_student = models.User(
                        full_name=student_data.full_name,
                        username=student_data.username,
                        social_id=None,
                        group_id=group.id,
                        role=models.UserRole.STUDENT,
                        is_active=True,
                        invite_code=invite_codes[i]
                    )
                    self.db.add(new_student)
            
            await self.db.commit()
            await self.db.refresh(group)
            return group

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error creating group: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Database error")
    
    async def _generate_unique_invite_codes_batch(self, count: int) -> List[str]:
        """Генерирует уникальные коды пачкой."""
        unique_codes = set()
        attempts = 0
        max_attempts = 10
        
        while len(unique_codes) < count and attempts < max_attempts:
            needed = count - len(unique_codes)
            # Generate slightly more to reduce chance of collision in one go
            batch = {self.generate_invite_code() for _ in range(needed + 2)}
            
            # Check existance in DB
            result = await self.db.execute(select(models.User.invite_code).where(models.User.invite_code.in_(batch)))
            existing_codes = set(result.scalars().all())
            
            # Add only non-existing
            available = batch - existing_codes
            unique_codes.update(available)
            attempts += 1
            
        if len(unique_codes) < count:
             raise HTTPException(status_code=500, detail="Could not generate unique invite codes")
             
        return list(unique_codes)[:count]

    async def _get_unique_invite_code(self) -> str:
        """Получить гарантированно уникальный инвайт-код."""
        codes = await self._generate_unique_invite_codes_batch(1)
        return codes[0]

    async def regenerate_user_code(self, user_id: UUID) -> str:
        """Регенерировать код студента."""
        result = await self.db.execute(select(models.User).where(models.User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
             raise HTTPException(status_code=404, detail="User not found")
        
        try:
            invite_code = await self._get_unique_invite_code()
            user.invite_code = invite_code
            await self.db.commit()
            return invite_code
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error regenerating user code: {e}")
            raise HTTPException(status_code=500, detail="Database error")

    async def regenerate_group_invite_code(self, group_id: UUID) -> str:
        """Сгенерировать/обновить инвайт-код группы."""
        result = await self.db.execute(select(models.Group).where(models.Group.id == group_id))
        group = result.scalar_one_or_none()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        try:
            # Генерируем уникальный код
            for _ in range(10):
                new_code = self.generate_invite_code()
                # Проверяем уникальность среди групп и пользователей
                existing_group = await self.db.execute(
                    select(models.Group).where(models.Group.invite_code == new_code)
                )
                existing_user = await self.db.execute(
                    select(models.User).where(models.User.invite_code == new_code)
                )
                if not existing_group.scalar_one_or_none() and not existing_user.scalar_one_or_none():
                    group.invite_code = new_code
                    await self.db.commit()
                    return new_code
            
            raise HTTPException(status_code=500, detail="Could not generate unique code")
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error regenerating group invite code: {e}")
            raise HTTPException(status_code=500, detail="Database error")

    async def regenerate_group_codes(self, group_id: UUID) -> dict:
        """Сгенерировать коды для всех студентов группы, у кого их нет."""
        result = await self.db.execute(select(models.User).where(models.User.group_id == group_id))
        students = result.scalars().all()
        
        students_without_code = [s for s in students if not s.invite_code]
        if not students_without_code:
            return {"generated": 0, "total_students": len(students)}

        try:
            invite_codes = await self._generate_unique_invite_codes_batch(len(students_without_code))
            
            for i, student in enumerate(students_without_code):
                student.invite_code = invite_codes[i]
                
            await self.db.commit()
            return {"generated": len(students_without_code), "total_students": len(students)}
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error regenerating group codes: {e}")
            raise HTTPException(status_code=500, detail="Database error")

