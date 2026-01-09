"""Attestation settings endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.core.limiter import limiter
from app.models import User, AttestationSettings
from app.services.attestation_service import AttestationService
from app.services.attestation.audit import AttestationAuditService
from app.schemas.attestation import (
    AttestationSettingsResponse,
    AttestationSettingsUpdate,
    AttestationType as AttestationTypeSchema,
)

router = APIRouter()


@router.get("/attestation/grade-scale/{attestation_type}")
async def get_grade_scale(
    attestation_type: AttestationTypeSchema,
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить шкалу оценок для типа аттестации."""
    return AttestationSettings.get_grade_scale(attestation_type)


@router.get("/attestation/settings/{attestation_type}", response_model=AttestationSettingsResponse)
async def get_attestation_settings(
    attestation_type: AttestationTypeSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить глобальные настройки аттестации."""
    service = AttestationService(db)
    settings = await service.get_or_create_settings(attestation_type)
    return service.to_response(settings)


@router.put("/attestation/settings", response_model=AttestationSettingsResponse)
@limiter.limit("5/minute")
async def update_attestation_settings(
    request: Request,
    settings_in: AttestationSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить глобальные настройки аттестации."""
    service = AttestationService(db)
    audit_service = AttestationAuditService(db)
    
    old_settings = await service.get_settings(settings_in.attestation_type)
    
    try:
        settings = await service.update_settings(settings_in)
        
        ip_address = request.client.host if request.client else None
        await audit_service.log_settings_change(
            attestation_type=settings_in.attestation_type,
            action="update" if old_settings else "create",
            old_settings=old_settings,
            new_settings=settings,
            changed_by_id=current_user.id,
            ip_address=ip_address
        )
        await db.commit()
        
        return service.to_response(settings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
