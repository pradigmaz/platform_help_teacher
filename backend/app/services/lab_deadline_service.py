"""Сервис для работы с продлениями дедлайнов лабораторных работ."""
import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lab import Lab
from app.models.lab_deadline_extension import LabDeadlineExtension
from app.models.group import Group
from app.schemas.deadline_extension import DeadlineExtensionCreate, DeadlineExtensionUpdate

logger = logging.getLogger(__name__)


class LabDeadlineService:
    """Сервис для управления продлениями дедлайнов лаб."""

    async def get_deadline_extensions(
        self,
        db: AsyncSession,
        lab_id: Optional[UUID] = None,
        group_id: Optional[UUID] = None,
        is_active: Optional[bool] = None
    ) -> List[LabDeadlineExtension]:
        """[LabDeadlineService:get_deadline_extensions] Получить продления дедлайнов с eager loading (решение N+1)."""
        query = select(LabDeadlineExtension).options(
            selectinload(LabDeadlineExtension.lab),
            selectinload(LabDeadlineExtension.group),
            selectinload(LabDeadlineExtension.creator)
        )
        
        if lab_id:
            query = query.where(LabDeadlineExtension.lab_id == lab_id)
        if group_id:
            query = query.where(LabDeadlineExtension.group_id == group_id)
        if is_active is not None:
            query = query.where(LabDeadlineExtension.is_active == is_active)
        
        query = query.order_by(LabDeadlineExtension.created_at.desc())
        
        result = await db.execute(query)
        extensions = result.scalars().all()
        logger.info(f"[LabDeadlineService:get_deadline_extensions] Found {len(extensions)} extensions (lab_id={lab_id}, group_id={group_id}, is_active={is_active})")
        return list(extensions)

    async def get_deadline_extension_by_id(
        self,
        db: AsyncSession,
        extension_id: UUID
    ) -> Optional[LabDeadlineExtension]:
        """[LabDeadlineService:get_deadline_extension_by_id] Получить продление по ID с eager loading."""
        result = await db.execute(
            select(LabDeadlineExtension)
            .options(
                selectinload(LabDeadlineExtension.lab),
                selectinload(LabDeadlineExtension.group),
                selectinload(LabDeadlineExtension.creator)
            )
            .where(LabDeadlineExtension.id == extension_id)
        )
        extension = result.scalar_one_or_none()
        logger.info(f"[LabDeadlineService:get_deadline_extension_by_id] Extension {extension_id} found: {extension is not None}")
        return extension

    async def create_deadline_extension(
        self,
        db: AsyncSession,
        ext_in: DeadlineExtensionCreate,
        created_by: UUID
    ) -> LabDeadlineExtension:
        """[LabDeadlineService:create_deadline_extension] Создать продление дедлайна с валидацией."""
        # Проверка существования лабы
        lab = await db.get(Lab, ext_in.lab_id)
        if not lab:
            logger.error(f"[LabDeadlineService:create_deadline_extension] Lab {ext_in.lab_id} not found")
            raise ValueError("Lab not found")
        
        # Проверка существования группы
        group = await db.get(Group, ext_in.group_id)
        if not group:
            logger.error(f"[LabDeadlineService:create_deadline_extension] Group {ext_in.group_id} not found")
            raise ValueError("Group not found")
        
        # Проверка на дубликат
        existing = await db.execute(
            select(LabDeadlineExtension).where(
                LabDeadlineExtension.lab_id == ext_in.lab_id,
                LabDeadlineExtension.group_id == ext_in.group_id
            )
        )
        if existing.scalar_one_or_none():
            logger.error(f"[LabDeadlineService:create_deadline_extension] Extension already exists for lab {ext_in.lab_id} and group {ext_in.group_id}")
            raise ValueError("Extension already exists for this lab and group")
        
        extension = LabDeadlineExtension(
            lab_id=ext_in.lab_id,
            group_id=ext_in.group_id,
            bonus_lessons=ext_in.bonus_lessons,
            reason=ext_in.reason,
            expires_at=ext_in.expires_at,
            created_by=created_by
        )
        db.add(extension)
        await db.commit()
        await db.refresh(extension)
        
        # Eager load relationships
        await db.refresh(extension, ["lab", "group", "creator"])
        
        logger.info(f"[LabDeadlineService:create_deadline_extension] Created extension for lab {lab.number} group {group.name}: +{ext_in.bonus_lessons} lessons")
        return extension

    async def update_deadline_extension(
        self,
        db: AsyncSession,
        extension: LabDeadlineExtension,
        ext_in: DeadlineExtensionUpdate
    ) -> LabDeadlineExtension:
        """[LabDeadlineService:update_deadline_extension] Обновить продление дедлайна."""
        update_data = ext_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(extension, field, value)
        
        await db.commit()
        await db.refresh(extension)
        
        # Eager load relationships
        await db.refresh(extension, ["lab", "group", "creator"])
        
        logger.info(f"[LabDeadlineService:update_deadline_extension] Updated extension {extension.id}: {update_data}")
        return extension

    async def delete_deadline_extension(
        self,
        db: AsyncSession,
        extension: LabDeadlineExtension
    ) -> None:
        """[LabDeadlineService:delete_deadline_extension] Удалить продление дедлайна."""
        extension_id = extension.id
        await db.delete(extension)
        await db.commit()
        logger.info(f"[LabDeadlineService:delete_deadline_extension] Deleted extension {extension_id}")


lab_deadline_service = LabDeadlineService()
