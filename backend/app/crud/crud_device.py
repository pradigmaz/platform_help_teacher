"""CRUD operations for Device model."""
import logging
from datetime import UTC, datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate

logger = logging.getLogger(__name__)


async def create(
    db: AsyncSession,
    *,
    user_id: UUID,
    device_in: DeviceCreate,
) -> Device:
    """Create a new device."""
    logger.info(f"[CRUD:create_device] Creating device for user_id={user_id}")

    now = datetime.now(UTC)
    device = Device(
        user_id=user_id,
        fingerprint_hash=device_in.fingerprint_hash,
        device_info=device_in.device_info,
        first_seen=now,
        last_seen=now,
    )

    db.add(device)
    await db.flush()
    await db.refresh(device)

    logger.info(f"[CRUD:create_device] Device created: id={device.id}")
    return device


async def get_by_id(
    db: AsyncSession,
    *,
    device_id: UUID,
) -> Device | None:
    """Get device by ID."""
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    return result.scalar_one_or_none()


async def get_by_user(
    db: AsyncSession,
    *,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[Device]:
    """Get all devices for a user."""
    result = await db.execute(
        select(Device)
        .where(Device.user_id == user_id)
        .order_by(Device.last_seen.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def count_by_user(
    db: AsyncSession,
    *,
    user_id: UUID,
) -> int:
    """Count devices for a user."""
    result = await db.execute(
        select(func.count()).select_from(Device).where(Device.user_id == user_id)
    )
    return result.scalar_one()


async def get_by_fingerprint(
    db: AsyncSession,
    *,
    user_id: UUID,
    fingerprint_hash: str,
) -> Device | None:
    """Get device by user ID and fingerprint hash."""
    result = await db.execute(
        select(Device).where(
            Device.user_id == user_id,
            Device.fingerprint_hash == fingerprint_hash,
        )
    )
    return result.scalar_one_or_none()


async def update(
    db: AsyncSession,
    *,
    device: Device,
    device_in: DeviceUpdate,
) -> Device:
    """Update device."""
    logger.info(f"[CRUD:update_device] Updating device: id={device.id}")

    update_data = device_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    device.updated_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(device)

    return device


async def delete_one(
    db: AsyncSession,
    *,
    device_id: UUID,
) -> bool:
    """Delete device by ID."""
    logger.info(f"[CRUD:delete_device] Deleting device: id={device_id}")

    device = await get_by_id(db, device_id=device_id)
    if not device:
        return False

    await db.delete(device)
    await db.flush()
    return True


async def bulk_delete_by_user(
    db: AsyncSession,
    *,
    user_id: UUID,
) -> int:
    """Delete all devices for a user in a single query. Returns count deleted."""
    logger.info(f"[CRUD:bulk_delete] Deleting all devices for user_id={user_id}")

    result = await db.execute(
        delete(Device).where(Device.user_id == user_id)
    )
    await db.flush()

    count = result.rowcount
    logger.info(f"[CRUD:bulk_delete] Deleted {count} devices for user_id={user_id}")
    return count
