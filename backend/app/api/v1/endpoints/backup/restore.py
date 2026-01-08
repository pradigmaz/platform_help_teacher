"""
Backup restore and verify operations.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.api.deps import get_current_active_superuser
from app.models import User
from app.schemas.backup import (
    RestoreRequest,
    RestoreResponse,
    VerifyResponse,
    validate_backup_key,
)
from app.services.backup import RestoreService
from app.core.limiter import limiter
from app.core.constants import RATE_LIMIT_BACKUP_RESTORE, RATE_LIMIT_BACKUP_VERIFY
from app.audit.decorators import audit_action
from app.audit.constants import ActionType, EntityType
from .deps import get_restore_service

logger = logging.getLogger(__name__)
router = APIRouter()


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
    Requires confirmation string: "RESTORE-{backup_key}"
    """
    backup_key = validate_backup_key(backup_key)
    
    expected_confirmation = f"RESTORE-{backup_key}"
    if data.confirmation != expected_confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid confirmation. Expected: '{expected_confirmation}'"
        )
    
    logger.warning(f"Restore initiated by {current_user.id}: {backup_key}")
    result = await service.restore_backup(backup_key, data.drop_existing)
    
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
    """Verify backup integrity without restoring."""
    backup_key = validate_backup_key(backup_key)
    valid = await service.verify_backup(backup_key)
    return VerifyResponse(valid=valid, backup_key=backup_key)
