"""Group settings and invite codes."""
from typing import Any
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app import schemas, models
from app.api import deps
from app.db.session import get_db
from app.services.group_service import GroupService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.patch("/{group_id}/lab-settings", response_model=schemas.GroupResponse)
async def update_lab_settings(
    group_id: UUID,
    lab_settings: schemas.LabSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Обновить настройки лабораторных для группы."""
    result = await db.execute(select(models.Group).where(models.Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    try:
        if lab_settings.labs_count is not None:
            group.labs_count = lab_settings.labs_count
        if lab_settings.grading_scale is not None:
            group.grading_scale = lab_settings.grading_scale
        if lab_settings.default_max_grade is not None:
            group.default_max_grade = lab_settings.default_max_grade
        
        await db.commit()
        await db.refresh(group)
        
        count_query = select(func.count(models.User.id)).where(models.User.group_id == group_id)
        count_result = await db.execute(count_query)
        students_count = count_result.scalar() or 0
        
        group_resp = schemas.GroupResponse.model_validate(group)
        group_resp.students_count = students_count
        return group_resp
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error updating lab settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error")


@router.post("/{group_id}/regenerate-invite-code")
async def regenerate_group_invite_code(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Сгенерировать/обновить инвайт-код группы."""
    service = GroupService(db)
    invite_code = await service.regenerate_group_invite_code(group_id)
    return {"invite_code": invite_code}


@router.post("/{group_id}/generate-codes")
async def regenerate_group_codes(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Сгенерировать коды для всех студентов группы."""
    service = GroupService(db)
    return await service.regenerate_group_codes(group_id)


@router.post("/users/{user_id}/regenerate-code")
async def regenerate_user_code(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Регенерировать код студента."""
    service = GroupService(db)
    invite_code = await service.regenerate_user_code(user_id)
    return {"invite_code": invite_code}
