"""Attestation audit endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.models import User
from app.services.attestation.audit import AttestationAuditService
from app.schemas.attestation import AttestationType as AttestationTypeSchema

router = APIRouter()


@router.get("/attestation/settings/audit")
async def get_settings_audit_history(
    attestation_type: Optional[AttestationTypeSchema] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить историю изменений настроек аттестации."""
    audit_service = AttestationAuditService(db)
    
    logs = await audit_service.get_audit_history(
        attestation_type=attestation_type,
        limit=limit
    )
    
    return [
        {
            "id": str(log.id),
            "settings_type": log.settings_type,
            "settings_key": log.settings_key,
            "action": log.action,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "changed_fields": log.changed_fields,
            "changed_by_id": str(log.changed_by_id) if log.changed_by_id else None,
            "changed_by_name": log.changed_by.full_name if log.changed_by else None,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
