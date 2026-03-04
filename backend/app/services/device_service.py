"""Device binding service."""

import hashlib
import json
import logging
from datetime import UTC, datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import crud_device
from app.schemas.device import DeviceCreate, DeviceUpdate

logger = logging.getLogger(__name__)


def hash_fingerprint(fingerprint: str) -> str:
    """Create SHA256 hash of device fingerprint."""
    return hashlib.sha256(fingerprint.encode()).hexdigest()


def parse_device_info(fingerprint_str: str | None) -> dict:
    """Parse device info from fingerprint JSON string.

    Supports dual-format input:
    - JSON object: extracts platform, browser, screen
    - Hash string (legacy/fallback): returns Unknown values without warning
    """
    if not fingerprint_str or fingerprint_str == "{}":
        logger.warning("[device_service:parse_device_info] Empty fingerprint")
        return {
            "platform": "Unknown",
            "browser": "Unknown",
            "screen": None,
        }

    try:
        fp = json.loads(fingerprint_str)
    except (json.JSONDecodeError, TypeError):
        # Hash string (e.g. "k7f2m1") — treat as legacy fingerprint, no warning
        return {
            "platform": "Unknown",
            "browser": "Unknown",
            "screen": None,
        }

    if not isinstance(fp, dict):
        # json.loads("0") → int, json.loads('"str"') → str, etc.
        return {
            "platform": "Unknown",
            "browser": "Unknown",
            "screen": None,
        }

    # Platform
    platform = fp.get("platform", "")
    if "Win" in platform:
        platform = "Windows"
    elif "Mac" in platform:
        platform = "macOS"
    elif "Linux" in platform:
        platform = "Linux"
    elif "Android" in platform:
        platform = "Android"
    elif "iPhone" in platform or "iPad" in platform:
        platform = "iOS"
    else:
        platform = platform or "Unknown"

    # Browser from userAgent
    ua = fp.get("userAgent", "")
    browser = "Unknown"
    if "Chrome" in ua and "Edg" not in ua:
        browser = "Chrome"
    elif "Firefox" in ua:
        browser = "Firefox"
    elif "Safari" in ua and "Chrome" not in ua:
        browser = "Safari"
    elif "Edg" in ua:
        browser = "Edge"
    elif "Opera" in ua or "OPR" in ua:
        browser = "Opera"

    # Screen
    screen_info = fp.get("screen", {})
    screen = None
    if screen_info:
        w = screen_info.get("width")
        h = screen_info.get("height")
        if w and h:
            screen = f"{w}×{h}"

    return {
        "platform": platform,
        "browser": browser,
        "screen": screen,
    }


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
        logger.warning(f"[device_service:register_or_update] Empty fingerprint for user {user_id}")
        return None

    try:
        fingerprint_hash = hash_fingerprint(device_fingerprint)
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
