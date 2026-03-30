"""
Backup settings, health check, and bot status.
"""

import logging
import shutil
from datetime import UTC, datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser
from app.core.config import settings
from app.db.session import get_db
from app.models import BackupSettings, User
from app.schemas.backup import (
    BackupFreshness,
    BackupHealthCheck,
    BackupHealthResponse,
    BackupOffsiteStatus,
    BackupSettingsSchema,
    BackupSettingsUpdate,
    BotStatusResponse,
)
from app.services.backup.backup_service import BackupService

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


def _merge_health_status(current: str, new_status: str) -> str:
    order = {"healthy": 0, "degraded": 1, "unhealthy": 2}
    return new_status if order[new_status] > order[current] else current


@router.get("/health", response_model=BackupHealthResponse)
async def backup_health_check(
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
    service: BackupService = Depends(get_backup_service),
):
    """Health check for backup system."""
    health_status = "healthy"
    freshness_status = "unknown"
    checks: dict[str, BackupHealthCheck] = {}
    expected_max_age_hours: float | None = None
    latest_created_at = None
    age_hours = None

    result = await db.execute(select(BackupSettings).where(BackupSettings.id == 1))
    db_settings = result.scalar_one_or_none() or BackupSettings(id=1)

    # 1. Check encryption key
    if not settings.BACKUP_ENCRYPTION_KEY or len(settings.BACKUP_ENCRYPTION_KEY) < 32:
        health_status = _merge_health_status(health_status, "unhealthy")
        checks["encryption_key"] = BackupHealthCheck(
            status="error",
            message="BACKUP_ENCRYPTION_KEY not configured or too short",
        )
    else:
        checks["encryption_key"] = BackupHealthCheck(status="ok")

    # 2. Check primary storage connectivity
    try:
        await service.storage.ensure_bucket()
        checks["primary_storage"] = BackupHealthCheck(status="ok")
    except Exception as e:
        health_status = _merge_health_status(health_status, "unhealthy")
        checks["primary_storage"] = BackupHealthCheck(status="error", message=str(e)[:100])

    # 3. Check offsite storage connectivity when configured
    offsite_configured = bool(service.offsite_storage)
    if service.offsite_storage:
        try:
            await service.offsite_storage.ensure_bucket()
            checks["offsite_storage"] = BackupHealthCheck(status="ok", configured=True)
        except Exception as e:
            health_status = _merge_health_status(health_status, "degraded")
            checks["offsite_storage"] = BackupHealthCheck(status="warning", message=str(e)[:100], configured=True)
    else:
        checks["offsite_storage"] = BackupHealthCheck(
            status="ok", configured=False, message="Offsite mirror is not configured"
        )

    # 4. Check pg_dump available
    pg_dump_path = shutil.which("pg_dump")
    if pg_dump_path:
        checks["pg_dump"] = BackupHealthCheck(status="ok", path=pg_dump_path)
    else:
        health_status = _merge_health_status(health_status, "unhealthy")
        checks["pg_dump"] = BackupHealthCheck(status="error", message="pg_dump not found")

    # 5. Get backup stats and freshness
    try:
        backups = await service.list_backups()
        latest = backups[0] if backups else None
        if latest:
            latest_created_at = latest.created_at
            latest_dt = latest.created_at
            if latest_dt.tzinfo is None:
                latest_dt = latest_dt.replace(tzinfo=UTC)
            age_hours = round((datetime.now(UTC) - latest_dt).total_seconds() / 3600, 2)

        if not db_settings.enabled:
            freshness_status = "disabled"
        elif not latest:
            freshness_status = "missing"
            expected_max_age_hours = 26.0
            health_status = _merge_health_status(health_status, "degraded")
        else:
            expected_max_age_hours = 26.0
            freshness_status = "fresh" if age_hours is not None and age_hours <= expected_max_age_hours else "stale"
            if freshness_status == "stale":
                health_status = _merge_health_status(health_status, "degraded")

        backups_status = "ok"
        backups_message = None
        latest_backup_mirrored = latest.offsite_present if latest else None
        if latest and offsite_configured and latest.offsite_present is False:
            backups_status = "warning"
            backups_message = "Latest backup is missing in offsite mirror"
            health_status = _merge_health_status(health_status, "degraded")

        checks["backups"] = BackupHealthCheck(
            status=backups_status,
            message=backups_message,
            count=len(backups),
            latest=latest.key if latest else None,
            latest_backup_mirrored=latest_backup_mirrored,
        )
    except Exception as e:
        freshness_status = "unknown"
        health_status = _merge_health_status(health_status, "degraded")
        checks["backups"] = BackupHealthCheck(status="warning", message=str(e)[:100])

    return BackupHealthResponse(
        status=health_status,
        checks=checks,
        freshness=BackupFreshness(
            status=freshness_status,
            latest_backup_key=checks["backups"].latest if "backups" in checks else None,
            latest_backup_at=latest_created_at if "latest_created_at" in locals() else None,
            age_hours=age_hours if "age_hours" in locals() else None,
            expected_max_age_hours=expected_max_age_hours,
            message=checks["backups"].message if "backups" in checks else None,
        ),
        offsite=BackupOffsiteStatus(
            configured=offsite_configured,
            status=checks["offsite_storage"].status if "offsite_storage" in checks else None,
            latest_backup_mirrored=checks["backups"].latest_backup_mirrored if "backups" in checks else None,
            message=checks["offsite_storage"].message if "offsite_storage" in checks else None,
        ),
    )


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
