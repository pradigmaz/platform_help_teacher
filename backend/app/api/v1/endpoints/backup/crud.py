"""
Backup CRUD operations: create, list, delete, upload.
"""

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

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
from app.services.backup import BackupService, RestoreService
from app.services.backup.restore_service import VERIFY_STATUS_RECOVERY_CODE_REQUIRED, VERIFY_STATUS_VALID

from .deps import get_backup_service, get_restore_service

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
        recovery_code=result.recovery_code,
        portable=bool(result.portable),
        format_version=result.format_version,
        key_fingerprint=result.key_fingerprint,
        created_with_current_key=result.created_with_current_key,
        size=result.size,
        uploaded=result.uploaded,
        mirrored_offsite=result.mirrored_offsite,
        offsite_error=result.offsite_error,
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
    recovery_code: str | None = Form(None),
    current_user: User = Depends(get_current_active_superuser),
    service: BackupService = Depends(get_backup_service),
    restore_service: RestoreService = Depends(get_restore_service),
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
        if await service.storage.exists(safe_filename):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Backup with this name already exists",
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".enc") as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            file_info = restore_service.encryption.inspect_file(tmp_path)
            verification = await restore_service.verify_local_backup(tmp_path, recovery_code)
            if verification.status not in {VERIFY_STATUS_VALID, VERIFY_STATUS_RECOVERY_CODE_REQUIRED}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=verification.error or em.INVALID_BACKUP_FORMAT,
                )

            object_metadata = {
                "backup-format-version": str(verification.format_version or file_info.format_version),
                "backup-portable": str(
                    bool(verification.portable if verification.portable is not None else file_info.portable)
                ).lower(),
            }
            if file_info.key_fingerprint:
                object_metadata["backup-key-fingerprint"] = file_info.key_fingerprint

            await service.storage.upload(tmp_path, safe_filename, object_metadata=object_metadata)
            mirrored_offsite = None
            offsite_error = None
            if service.offsite_storage:
                try:
                    await service.offsite_storage.upload(tmp_path, safe_filename, object_metadata=object_metadata)
                    mirrored_offsite = True
                except Exception as exc:
                    mirrored_offsite = False
                    offsite_error = str(exc).strip() or "Offsite mirror failed"
                    logger.error("Offsite mirror failed for uploaded backup %s: %s", safe_filename, offsite_error)

            version = verification.format_version or file_info.format_version
            logger.info("Backup uploaded by %s: %s (v%s)", current_user.id, safe_filename, version)
            return UploadBackupResponse(
                success=True,
                backup_key=safe_filename,
                size=len(content),
                verified=verification.valid,
                verification_status=verification.status,
                format_version=version,
                portable=verification.portable if verification.portable is not None else file_info.portable,
                created_with_current_key=verification.created_with_current_key,
                mirrored_offsite=mirrored_offsite,
                offsite_error=offsite_error,
            )
        finally:
            tmp_path.unlink(missing_ok=True)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return UploadBackupResponse(success=False, error=str(e)[:200])
