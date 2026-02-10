from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.api import deps
from app.db.session import get_db
from app.models import User
from app.services.lab_settings_service import lab_settings_service

router = APIRouter()


@router.get("/lab-settings", response_model=schemas.LabSettingsResponse)
async def get_lab_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить глобальные настройки лабораторных."""
    settings = await lab_settings_service.get_lab_settings(db)

    if not settings:
        # Возвращаем дефолтные значения без сохранения, is_configured=False
        return schemas.LabSettingsResponse(
            labs_count=10,
            grading_scale="10",
            default_max_grade=10,
            is_configured=False,
        )

    return settings


@router.patch("/lab-settings", response_model=schemas.LabSettingsResponse)
async def update_lab_settings(
    settings_in: schemas.LabSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить глобальные настройки лабораторных."""
    settings = await lab_settings_service.update_lab_settings(db, settings_in)
    return settings
