"""
Backup settings, health check, and bot status.
"""
import logging
import shutil
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser
from app.db.session import get_db
from app.models import User, BackupSettings
from app.core.config import settings
from app.schemas.backup import (
    BackupSettingsSchema,
    BackupSettingsUpdate,
    BotStatusResponse,
)
from app.services.backup import BackupService
from .deps import get_backup_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/settings", response_model=BackupSettingsSchema)
async def get_backup_settings(
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Get current backup settings."""
    result = await db.execute(select(BackupSettings).where(BackupSettings.id == 1))
    db_settings = result.scalar_one_or_none()
    
    if not db_settings:
        return BackupSettingsSchema()
    
    return BackupSettingsSchema.model_validate(db_settings)


@router.put("/settings", response_model=BackupSettingsSchema)
async def update_backup_settings(
    data: BackupSettingsUpdate,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Update backup settings."""
    result = await db.execute(select(BackupSettings).where(BackupSettings.id == 1))
    db_settings = result.scalar_one_or_none()
    
    if not db_settings:
        db_settings = BackupSettings(id=1)
        db.add(db_settings)
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_settings, field, value)
    
    await db.commit()
    await db.refresh(db_settings)
    
    logger.info(f"Backup settings updated by {current_user.id}: {update_data}")
    return BackupSettingsSchema.model_validate(db_settings)


@router.get("/health")
async def backup_health_check(
    current_user: User = Depends(get_current_active_superuser),
    service: BackupService = Depends(get_backup_service),
):
    """Health check for backup system."""
    health = {"status": "healthy", "checks": {}}
    
    # 1. Check encryption key
    if not settings.BACKUP_ENCRYPTION_KEY or len(settings.BACKUP_ENCRYPTION_KEY) < 32:
        health["status"] = "unhealthy"
        health["checks"]["encryption_key"] = {
            "status": "error",
            "message": "BACKUP_ENCRYPTION_KEY not configured or too short"
        }
    else:
        health["checks"]["encryption_key"] = {"status": "ok"}
    
    # 2. Check MinIO connectivity
    try:
        await service.storage.ensure_bucket()
        health["checks"]["storage"] = {"status": "ok"}
    except Exception as e:
        health["status"] = "unhealthy"
        health["checks"]["storage"] = {"status": "error", "message": str(e)[:100]}
    
    # 3. Check pg_dump available
    pg_dump_path = shutil.which("pg_dump")
    if pg_dump_path:
        health["checks"]["pg_dump"] = {"status": "ok", "path": pg_dump_path}
    else:
        health["status"] = "unhealthy"
        health["checks"]["pg_dump"] = {"status": "error", "message": "pg_dump not found"}
    
    # 4. Get backup stats
    try:
        backups = await service.list_backups()
        health["checks"]["backups"] = {
            "status": "ok",
            "count": len(backups),
            "latest": backups[0].key if backups else None,
        }
    except Exception as e:
        health["checks"]["backups"] = {"status": "warning", "message": str(e)[:100]}
    
    return health


@router.get("/bot-status", response_model=BotStatusResponse)
async def get_bot_status(
    current_user: User = Depends(get_current_active_superuser),
):
    """Get status of available notification bots."""
    telegram_available = bool(settings.TELEGRAM_BOT_TOKEN)
    vk_available = bool(settings.VK_BOT_TOKEN and settings.VK_GROUP_ID)
    
    return BotStatusResponse(
        telegram_available=telegram_available,
        vk_available=vk_available,
        telegram_admin_id=settings.FIRST_SUPERUSER_ID if telegram_available else None,
        vk_admin_id=None,
    )
