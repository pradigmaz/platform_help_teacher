"""
Backup CRUD operations: create, list, delete, upload.
"""

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from app.api.deps import get_current_active_superuser
from app.audit.constants import ActionType, EntityType
from app.audit.decorators import audit_action
from app.core import error_messages as em
from app.core.constants import RATE_LIMIT_BACKUP_CREATE, RATE_LIMIT_BACKUP_DELETE
from app.core.limiter import limiter
from app.models import User
from app.schemas.backup import (
    MAX_BACKUP_UPLOAD_SIZE,
    BackupCreate,
    BackupCreateResponse,
    BackupInfo,
    BackupListResponse,
    UploadBackupResponse,
    validate_backup_key,
)
from app.services.backup import BackupService

from .deps import get_backup_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=BackupCreateResponse)
@limiter.limit(RATE_LIMIT_BACKUP_CREATE)
@audit_action(ActionType.BACKUP_CREATE, EntityType.BACKUP)
async def create_backup(
    request: Request,
    data: BackupCreate = None,
    current_user: User = Depends(get_current_active_superuser),
    service: BackupService = Depends(get_backup_service),
):
    """Create encrypted backup of the database."""
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
        uploaded=result.uploaded,
        notification_sent=result.notification_sent,
        notification_error=result.notification_error,
        error=result.error,
    )


@router.get("/", response_model=BackupListResponse)
@audit_action(ActionType.VIEW, EntityType.BACKUP)
async def list_backups(
    request: Request,
    current_user: User = Depends(get_current_active_superuser),
    service: BackupService = Depends(get_backup_service),
):
    """List all available backups."""
    backups = await service.list_backups()
    return BackupListResponse(
        backups=[BackupInfo(name=b.name, key=b.key, size=b.size, created_at=b.created_at) for b in backups],
        total=len(backups),
    )


@router.delete("/{backup_key}")
@limiter.limit(RATE_LIMIT_BACKUP_DELETE)
@audit_action(ActionType.BACKUP_DELETE, EntityType.BACKUP)
async def delete_backup(
    backup_key: str,
    request: Request,
    current_user: User = Depends(get_current_active_superuser),
    service: BackupService = Depends(get_backup_service),
):
    """Delete a backup."""
    backup_key = validate_backup_key(backup_key)
    success = await service.delete_backup(backup_key)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=em.BACKUP_NOT_FOUND,
        )

    logger.info(f"Backup deleted by {current_user.id}: {backup_key}")
    return {"status": "deleted", "backup_key": backup_key}


@router.post("/upload", response_model=UploadBackupResponse)
@limiter.limit("5/hour")
@audit_action(ActionType.BACKUP_CREATE, EntityType.BACKUP)
async def upload_backup(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_superuser),
    service: BackupService = Depends(get_backup_service),
):
    """Upload encrypted backup file to storage. Max size: 50MB."""
    if not file.filename or not file.filename.endswith(".enc"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=em.FILE_MUST_HAVE_ENC_EXTENSION)

    content = await file.read()
    if len(content) > MAX_BACKUP_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {MAX_BACKUP_UPLOAD_SIZE // (1024 * 1024)}MB",
        )

    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=em.EMPTY_FILE)

    # Minimum size for v1: header(25) + tag(16)
    MIN_ENCRYPTED_SIZE = 25 + 16
    if len(content) < MIN_ENCRYPTED_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=em.FILE_TOO_SMALL)

    try:
        safe_filename = validate_backup_key(file.filename)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".enc") as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            if not service.encryption.verify_file(tmp_path):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=em.INVALID_BACKUP_FORMAT)

            await service.storage.upload(tmp_path, safe_filename)
            version = service.encryption.get_file_version(tmp_path)
            logger.info(f"Backup uploaded by {current_user.id}: {safe_filename} (v{version})")
            return UploadBackupResponse(success=True, backup_key=safe_filename, size=len(content))
        finally:
            tmp_path.unlink(missing_ok=True)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return UploadBackupResponse(success=False, error=str(e)[:200])
