"""Device binding service."""

import hashlib
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import crud_device
from app.fingerprint_contract import build_device_info, compute_fingerprint_digest, parse_fingerprint_payload
from app.schemas.device import DeviceCreate, DeviceUpdate

logger = logging.getLogger(__name__)


def hash_fingerprint(fingerprint: str) -> str:
    """Create a backward-compatible device-binding digest for accepted fingerprint input."""
    envelope = parse_fingerprint_payload(fingerprint)
    if not envelope:
        return ""
    if envelope.get("kind") == "missing":
        return ""

    if envelope.get("kind") == "normalized_replacement":
        return compute_fingerprint_digest(envelope) or ""

    raw_fingerprint = fingerprint.strip()
    if not raw_fingerprint:
        return ""
    return hashlib.sha256(raw_fingerprint.encode()).hexdigest()


def parse_device_info(fingerprint_str: str | None) -> dict:
    """Parse device info from any accepted fingerprint input."""
    if not fingerprint_str or fingerprint_str == "{}":
        logger.debug("[device_service:parse_device_info] Empty fingerprint tolerated")
    return build_device_info(fingerprint_str)


async def register_or_update_device(
    db: AsyncSession,
    user_id: UUID,
    device_fingerprint: str | None,
) -> bool | None:
    """
    Register or update device on login.

    Args:
        db: Database session
        user_id: User ID
        device_fingerprint: Device fingerprint JSON string

    Returns:
        True if device was registered/updated successfully,
        False if an error occurred,
        None if fingerprint is empty (early return, no operation performed).
    """
    if not device_fingerprint or device_fingerprint == "{}":
        logger.debug("[device_service:register_or_update] Empty fingerprint tolerated for user %s", user_id)
        return None

    try:
        fingerprint_hash = hash_fingerprint(device_fingerprint)
        if not fingerprint_hash:
            logger.debug("[device_service:register_or_update] Missing digest tolerated for user %s", user_id)
            return None
        device_info = parse_device_info(device_fingerprint)

        logger.info(
            f"[device_service:register_or_update] Processing device for user {user_id}, hash={fingerprint_hash[:8]}..."
        )

        # Check if device exists
        existing_device = await crud_device.get_by_fingerprint(db, user_id=user_id, fingerprint_hash=fingerprint_hash)

        if existing_device:
            # Update last_seen
            device_update = DeviceUpdate(
                last_seen=datetime.now(UTC),
                device_info=device_info,
            )
            await crud_device.update(db, device=existing_device, device_in=device_update)
            logger.info(f"[device_service:register_or_update] Updated device {existing_device.id} for user {user_id}")
        else:
            # Create new device
            device_create = DeviceCreate(fingerprint_hash=fingerprint_hash, device_info=device_info)
            new_device = await crud_device.create(db, user_id=user_id, device_in=device_create)
            logger.info(f"[device_service:register_or_update] Created device {new_device.id} for user {user_id}")

        await db.commit()
        return True

    except Exception as e:
        logger.error(
            f"[device_service:register_or_update] Error processing device for user {user_id}: {e}", exc_info=True
        )
        await db.rollback()
        return False
