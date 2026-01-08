"""
Admin API endpoints for backup management.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser
from app.db.session import get_db
from app.models import User
from app.schemas.backup import (
    BackupCreate,
    BackupInfo,
    BackupListResponse,
    BackupCreateResponse,
    RestoreRequest,
    RestoreResponse,
    VerifyResponse,
    BackupSettingsSchema,
    BackupSettingsUpdate,
    validate_backup_key,
)
from app.services.backup import BackupService, RestoreService
from app.models import BackupSettings
from app.core.limiter import limiter
from app.core.constants import (
    RATE_LIMIT_BACKUP_CREATE,
    RATE_LIMIT_BACKUP_RESTORE,
    RATE_LIMIT_BACKUP_DELETE,
    RATE_LIMIT_BACKUP_VERIFY,
)
from app.audit.decorators import audit_action
from app.audit.constants import ActionType, EntityType

logger = logging.getLogger(__name__)
router = APIRouter()


def get_backup_service() -> BackupService:
    """Dependency for backup service."""
    return BackupService()


def get_restore_service() -> RestoreService:
    """Dependency for restore service."""
    return RestoreService()


@router.post("", response_model=BackupCreateResponse)
@limiter.limit(RATE_LIMIT_BACKUP_CREATE)
@audit_action(ActionType.BACKUP_CREATE, EntityType.BACKUP)
async def create_backup(
    request: Request,
    data: BackupCreate = None,
    current_user: User = Depends(get_current_active_superuser),
    service: BackupService = Depends(get_backup_service),
):
    """
    Create encrypted backup of the database.
    Only admins can create backups.
    Rate limited: 3/hour.
    """
    name = data.name if data else None
    result = await service.create_backup(name)
    
    if not result.success:
        logger.error(f"Backup failed by {current_user.id}: {result.error}")
    else:
        logger.info(f"Backup created by {current_user.id}: {result.backup_key}")
    
    return BackupCreateResponse(
        success=result.success,
        backup_key=result.backup_key,
        size=result.size,
        error=result.error,
    )


@router.get("", response_model=BackupListResponse)
@audit_action(ActionType.VIEW, EntityType.BACKUP)
async def list_backups(
    request: Request,
    current_user: User = Depends(get_current_active_superuser),
    service: BackupService = Depends(get_backup_service),
):
    """
    List all available backups.
    Only admins can view backups.
    """
    backups = await service.list_backups()
    return BackupListResponse(
        backups=[
            BackupInfo(
                name=b.name,
                key=b.key,
                size=b.size,
                created_at=b.created_at,
            )
            for b in backups
        ],
        total=len(backups),
    )


@router.post("/{backup_key}/restore", response_model=RestoreResponse)
@limiter.limit(RATE_LIMIT_BACKUP_RESTORE)
@audit_action(ActionType.BACKUP_RESTORE, EntityType.BACKUP)
async def restore_backup(
    backup_key: str,
    request: Request,
    data: RestoreRequest,
    current_user: User = Depends(get_current_active_superuser),
    service: RestoreService = Depends(get_restore_service),
):
    """
    Restore database from encrypted backup.
    WARNING: This will overwrite existing data!
    Only admins can restore backups.
    Rate limited: 2/hour.
    
    Requires confirmation string: "RESTORE-{backup_key}"
    """
    # Validate backup_key to prevent path traversal
    backup_key = validate_backup_key(backup_key)
    
    # Verify confirmation token (prevents accidental restores)
    expected_confirmation = f"RESTORE-{backup_key}"
    if data.confirmation != expected_confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid confirmation. Expected: '{expected_confirmation}'"
        )
    
    drop_existing = data.drop_existing
    
    logger.warning(f"Restore initiated by {current_user.id}: {backup_key}")
    result = await service.restore_backup(backup_key, drop_existing)
    
    if result.success:
        logger.info(f"Restore completed: {backup_key}")
    else:
        logger.error(f"Restore failed: {result.error}")
    
    return RestoreResponse(success=result.success, error=result.error)


@router.post("/{backup_key}/verify", response_model=VerifyResponse)
@limiter.limit(RATE_LIMIT_BACKUP_VERIFY)
@audit_action(ActionType.BACKUP_VERIFY, EntityType.BACKUP)
async def verify_backup(
    backup_key: str,
    request: Request,
    current_user: User = Depends(get_current_active_superuser),
    service: RestoreService = Depends(get_restore_service),
):
    """
    Verify backup integrity without restoring.
    Downloads and decrypts to verify, but doesn't restore.
    Rate limited: 10/hour.
    """
    # Validate backup_key to prevent path traversal
    backup_key = validate_backup_key(backup_key)
    
    valid = await service.verify_backup(backup_key)
    return VerifyResponse(valid=valid, backup_key=backup_key)


@router.delete("/{backup_key}")
@limiter.limit(RATE_LIMIT_BACKUP_DELETE)
@audit_action(ActionType.BACKUP_DELETE, EntityType.BACKUP)
async def delete_backup(
    backup_key: str,
    request: Request,
    current_user: User = Depends(get_current_active_superuser),
    service: BackupService = Depends(get_backup_service),
):
    """
    Delete a backup.
    Only admins can delete backups.
    Rate limited: 10/hour.
    """
    # Validate backup_key to prevent path traversal
    backup_key = validate_backup_key(backup_key)
    
    success = await service.delete_backup(backup_key)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup not found or delete failed",
        )
    
    logger.info(f"Backup deleted by {current_user.id}: {backup_key}")
    return {"status": "deleted", "backup_key": backup_key}


@router.get("/settings", response_model=BackupSettingsSchema)
async def get_backup_settings(
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current backup settings.
    """
    from sqlalchemy import select
    result = await db.execute(select(BackupSettings).where(BackupSettings.id == 1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Return defaults if not configured
        return BackupSettingsSchema()
    
    return BackupSettingsSchema.model_validate(settings)


@router.get("/health")
async def backup_health_check(
    current_user: User = Depends(get_current_active_superuser),
    service: BackupService = Depends(get_backup_service),
):
    """
    Health check for backup system.
    Verifies:
    - MinIO/S3 storage connectivity
    - Encryption key validity
    - pg_dump availability
    """
    import shutil
    from app.core.config import settings
    
    health = {
        "status": "healthy",
        "checks": {},
    }
    
    # 1. Check encryption key configured
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
        health["checks"]["storage"] = {
            "status": "error",
            "message": str(e)[:100]
        }
    
    # 3. Check pg_dump available
    pg_dump_path = shutil.which("pg_dump")
    if pg_dump_path:
        health["checks"]["pg_dump"] = {"status": "ok", "path": pg_dump_path}
    else:
        health["status"] = "unhealthy"
        health["checks"]["pg_dump"] = {
            "status": "error",
            "message": "pg_dump not found in PATH"
        }
    
    # 4. Get backup stats
    try:
        backups = await service.list_backups()
        health["checks"]["backups"] = {
            "status": "ok",
            "count": len(backups),
            "latest": backups[0].key if backups else None,
        }
    except Exception as e:
        health["checks"]["backups"] = {
            "status": "warning",
            "message": str(e)[:100]
        }
    
    return health


@router.put("/settings", response_model=BackupSettingsSchema)
async def update_backup_settings(
    data: BackupSettingsUpdate,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Update backup settings.
    """
    from sqlalchemy import select
    result = await db.execute(select(BackupSettings).where(BackupSettings.id == 1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create with defaults + updates
        settings = BackupSettings(id=1)
        db.add(settings)
    
    # Apply updates
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    await db.commit()
    await db.refresh(settings)
    
    logger.info(f"Backup settings updated by {current_user.id}: {update_data}")
    return BackupSettingsSchema.model_validate(settings)
