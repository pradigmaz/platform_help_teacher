from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.models import User
from app.schemas.deadline_extension import (
    DeadlineExtensionCreate, DeadlineExtensionUpdate,
    DeadlineExtensionResponse, DeadlineExtensionListResponse
)
from app.services.lab_deadline_service import lab_deadline_service

router = APIRouter()


def _build_extension_response(ext) -> DeadlineExtensionResponse:
    """Построить ответ из модели deadline extension с eager-loaded relationships."""
    return DeadlineExtensionResponse(
        id=ext.id,
        lab_id=ext.lab_id,
        group_id=ext.group_id,
        bonus_lessons=ext.bonus_lessons,
        reason=ext.reason,
        expires_at=ext.expires_at,
        is_active=ext.is_active,
        created_by=ext.created_by,
        created_at=ext.created_at,
        updated_at=ext.updated_at,
        lab_number=ext.lab.number if ext.lab else None,
        lab_title=ext.lab.title if ext.lab else None,
        group_name=ext.group.name if ext.group else None,
        creator_name=ext.creator.full_name if ext.creator else None,
    )


@router.get("/deadline-extensions", response_model=DeadlineExtensionListResponse)
async def get_deadline_extensions(
    lab_id: Optional[UUID] = Query(default=None),
    group_id: Optional[UUID] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить список продлений дедлайнов."""
    extensions = await lab_deadline_service.get_deadline_extensions(db, lab_id, group_id, is_active)

    items = [_build_extension_response(ext) for ext in extensions]
    return DeadlineExtensionListResponse(items=items, total=len(items))


@router.post("/deadline-extensions", response_model=DeadlineExtensionResponse)
async def create_deadline_extension(
    ext_in: DeadlineExtensionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Создать продление дедлайна для группы."""
    try:
        extension = await lab_deadline_service.create_deadline_extension(db, ext_in, current_user.id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        elif "already exists" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)

    return _build_extension_response(extension)


@router.patch("/deadline-extensions/{extension_id}", response_model=DeadlineExtensionResponse)
async def update_deadline_extension(
    extension_id: UUID,
    ext_in: DeadlineExtensionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить продление дедлайна."""
    extension = await lab_deadline_service.get_deadline_extension_by_id(db, extension_id)
    if not extension:
        raise HTTPException(status_code=404, detail="Extension not found")

    extension = await lab_deadline_service.update_deadline_extension(db, extension, ext_in)
    return _build_extension_response(extension)


@router.delete("/deadline-extensions/{extension_id}")
async def delete_deadline_extension(
    extension_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Удалить продление дедлайна."""
    extension = await lab_deadline_service.get_deadline_extension_by_id(db, extension_id)
    if not extension:
        raise HTTPException(status_code=404, detail="Extension not found")

    await lab_deadline_service.delete_deadline_extension(db, extension)
    return {"status": "deleted"}
