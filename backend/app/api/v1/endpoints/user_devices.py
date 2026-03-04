"""User device management endpoints."""

import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.audit import ActionType, EntityType, audit_action
from app.core.limiter import limiter
from app.crud import crud_device
from app.db.session import get_db
from app.models import User
from app.schemas.device import (
    DeviceListResponse,
    DevicePublicResponse,
    DeviceUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def _get_user_device(
    db: AsyncSession, device_id: UUID, user_id: UUID
):
    """Get device and verify ownership. Raises HTTPException if not found/forbidden."""
    device = await crud_device.get_by_id(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найдено",
        )
    if device.user_id != user_id:
        logger.warning(
            f"[user_devices] User {user_id} attempted to access device {device_id} "
            f"owned by {device.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён",
        )
    return device


@router.get("/me/devices", response_model=DeviceListResponse)
@limiter.limit("20/minute")
async def get_my_devices(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeviceListResponse:
    """Get all devices bound to current user."""
    logger.info(f"[user_devices:get_my_devices] User {current_user.id} requesting devices")

    devices = await crud_device.get_by_user(db, user_id=current_user.id)
    total = await crud_device.count_by_user(db, user_id=current_user.id)

    return DeviceListResponse(
        devices=[DevicePublicResponse.model_validate(d) for d in devices],
        total=total,
    )


@router.get("/me/devices/{device_id}", response_model=DevicePublicResponse)
@limiter.limit("30/minute")
async def get_device(
    request: Request,
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DevicePublicResponse:
    """Get specific device by ID."""
    device = await _get_user_device(db, device_id, current_user.id)
    return DevicePublicResponse.model_validate(device)


@router.delete("/me/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
@audit_action(ActionType.DELETE, EntityType.PROFILE)
async def unbind_device(
    request: Request,
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Unbind (delete) a device from current user."""
    logger.info(f"[user_devices:unbind_device] User {current_user.id} unbinding device {device_id}")

    await _get_user_device(db, device_id, current_user.id)

    success = await crud_device.delete_one(db, device_id=device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось отвязать устройство",
        )
    await db.commit()


@router.post("/me/devices/{device_id}/confirm", response_model=DevicePublicResponse)
@limiter.limit("10/minute")
@audit_action(ActionType.UPDATE, EntityType.PROFILE)
async def confirm_device(
    request: Request,
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DevicePublicResponse:
    """Confirm device binding (mark as trusted)."""
    logger.info(f"[user_devices:confirm_device] User {current_user.id} confirming device {device_id}")

    device = await _get_user_device(db, device_id, current_user.id)

    if device.is_trusted:
        return DevicePublicResponse.model_validate(device)

    device_update = DeviceUpdate(
        is_trusted=True,
        confirmed_at=datetime.now(timezone.utc),
    )
    updated = await crud_device.update(db, device=device, device_in=device_update)
    await db.commit()
    return DevicePublicResponse.model_validate(updated)


@router.post("/me/devices/revoke-all", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
@audit_action(ActionType.DELETE, EntityType.PROFILE)
async def revoke_all_devices(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Unbind all devices from current user."""
    logger.info(f"[user_devices:revoke_all_devices] User {current_user.id} revoking all devices")

    count = await crud_device.bulk_delete_by_user(db, user_id=current_user.id)
    await db.commit()

    return {
        "revoked_count": count,
        "message": f"Отвязано устройств: {count}",
    }
