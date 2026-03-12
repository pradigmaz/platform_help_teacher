"""
Backup restore and verify operations.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import get_current_active_superuser
from app.audit.constants import ActionType, EntityType
from app.audit.decorators import audit_action
from app.core.config import settings
from app.core.constants import RATE_LIMIT_BACKUP_RESTORE, RATE_LIMIT_BACKUP_VERIFY
from app.core.limiter import limiter
from app.models import User
from app.schemas.backup import (
    RestoreRequest,
    RestoreResponse,
    VerifyRequest,
    VerifyResponse,
    validate_backup_key,
)
from app.services.backup import RestoreService

from .deps import get_restore_service

logger = logging.getLogger(__name__)
router = APIRouter()
RESTORE_RATE_LIMIT = "30/minute" if settings.ENVIRONMENT == "development" else RATE_LIMIT_BACKUP_RESTORE


@router.post("/{backup_key}/restore", response_model=RestoreResponse)
@limiter.limit(RESTORE_RATE_LIMIT)
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
    Requires confirmation string: "RESTORE-{backup_key}"
    """
    backup_key = validate_backup_key(backup_key)

    expected_confirmation = f"RESTORE-{backup_key}"
    if data.confirmation != expected_confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid confirmation. Expected: '{expected_confirmation}'"
        )

    logger.warning(f"Restore initiated by {current_user.id}: {backup_key}")
    result = await service.restore_backup(backup_key, data.drop_existing, data.recovery_code)

    if result.success:
        logger.info(f"Restore completed: {backup_key}")
    else:
        logger.error(f"Restore failed: {result.error}")

    return RestoreResponse(
        success=result.success,
        status=result.status,
        error=result.error,
        format_version=result.format_version,
        portable=result.portable,
        created_with_current_key=result.created_with_current_key,
        offsite_used=result.offsite_used,
    )


@router.post("/{backup_key}/verify", response_model=VerifyResponse)
@limiter.limit(RATE_LIMIT_BACKUP_VERIFY)
@audit_action(ActionType.BACKUP_VERIFY, EntityType.BACKUP)
async def verify_backup(
    backup_key: str,
    request: Request,
    data: VerifyRequest | None = None,
    current_user: User = Depends(get_current_active_superuser),
    service: RestoreService = Depends(get_restore_service),
):
    """Verify backup integrity without restoring."""
    backup_key = validate_backup_key(backup_key)
    result = await service.verify_backup(backup_key, data.recovery_code if data else None)
    return VerifyResponse(
        valid=result.valid,
        backup_key=backup_key,
        status=result.status,
        error=result.error,
        format_version=result.format_version,
        portable=result.portable,
        created_with_current_key=result.created_with_current_key,
        offsite_used=result.offsite_used,
    )
