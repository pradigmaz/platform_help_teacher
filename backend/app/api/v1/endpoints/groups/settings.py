"""Group settings and invite codes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.db.session import get_db
from app.services.group_service import GroupService

router = APIRouter()


@router.patch("/{group_id}/lab-settings", response_model=schemas.GroupResponse)
async def update_lab_settings(
    group_id: UUID,
    lab_settings: schemas.LabSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Не изменять legacy-настройки группы после перехода на policy связок."""
    raise HTTPException(
        status_code=410,
        detail="Групповые настройки лабораторных доступны только как legacy fallback. Используйте настройки связки группа / предмет / семестр.",
    )


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
