"""User session management endpoints."""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_current_user
from app.audit import ActionType, EntityType, audit_action
from app.audit.middleware import SESSION_COOKIE_NAME
from app.core.config import settings
from app.core.limiter import limiter
from app.models import User
from app.schemas.session import DeviceInfo, RevokeSessionsResponse, SessionListResponse, SessionResponse
from app.fingerprint_contract import build_device_info
from app.services import session_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _parse_device_info(device_payload: dict | str | None) -> DeviceInfo:
    """Parse device info from stored device summary or legacy fingerprint JSON."""
    if not device_payload:
        return DeviceInfo()

    raw_payload = device_payload
    if not isinstance(device_payload, dict):
        try:
            raw_payload = json.loads(device_payload)
        except (json.JSONDecodeError, TypeError):
            raw_payload = device_payload

    if isinstance(raw_payload, dict) and isinstance(raw_payload.get("browser"), str):
        screen = raw_payload.get("screen") if isinstance(raw_payload.get("screen"), dict) else {}
        width = screen.get("width")
        height = screen.get("height")
        return DeviceInfo(
            platform=raw_payload.get("platform"),
            browser=raw_payload.get("browser") or raw_payload.get("userAgent"),
            screen=f"{width}×{height}" if width and height else None,
        )

    device_info = build_device_info(raw_payload)
    return DeviceInfo(
        platform=device_info.get("platform"),
        browser=device_info.get("browser"),
        screen=device_info.get("screen"),
    )


def _mask_ip(ip: str | None) -> str | None:
    """Mask IP address for privacy (show only first two octets)."""
    if not ip:
        return None
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.x.x"
    return ip[:8] + "..."  # IPv6 or other


@router.get("/me/sessions", response_model=SessionListResponse)
@limiter.limit("10/minute")
async def get_my_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> SessionListResponse:
    """Get all active sessions for current user."""
    current_session_id = request.cookies.get(SESSION_COOKIE_NAME)
    sessions_data = await session_service.get_user_sessions(current_user.id)

    sessions = []
    for s in sessions_data:
        # Skip impersonation sessions
        if s.get("is_impersonation"):
            continue

        session_id = s.get("session_id", "")
        created_at_str = s.get("created_at")

        try:
            created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now()
        except ValueError:
            created_at = datetime.now()

        sessions.append(
            SessionResponse(
                session_id=session_id,
                created_at=created_at,
                ip_address=_mask_ip(s.get("ip_address")),
                device=_parse_device_info(s.get("device_summary") or s.get("device_fingerprint")),
                is_current=(session_id == current_session_id),
            )
        )

    # Sort: current first, then by created_at desc
    sessions.sort(key=lambda x: (x.is_current, x.created_at), reverse=True)

    return SessionListResponse(
        sessions=sessions,
        total=len(sessions),
        max_sessions=settings.MAX_ACTIVE_SESSIONS,
    )


@router.delete("/me/sessions/{session_id}")
@limiter.limit("10/minute")
@audit_action(ActionType.AUTH_LOGOUT, EntityType.AUTH)
async def revoke_session(
    request: Request,
    session_id: str,
    current_user: User = Depends(get_current_user),
) -> RevokeSessionsResponse:
    """Revoke a specific session (logout from device)."""
    current_session_id = request.cookies.get(SESSION_COOKIE_NAME)

    # Can't revoke current session via this endpoint
    if session_id == current_session_id:
        raise HTTPException(status_code=400, detail="Нельзя завершить текущую сессию. Используйте выход из аккаунта.")

    # Check ownership
    owner_id = await session_service.get_session_owner(session_id)
    if owner_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    success = await session_service.revoke_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    logger.info(f"User {current_user.id} revoked session {session_id[:8]}...")

    return RevokeSessionsResponse(revoked_count=1, message="Сессия завершена")


@router.post("/me/sessions/revoke-all")
@limiter.limit("5/minute")
@audit_action(ActionType.AUTH_LOGOUT, EntityType.AUTH)
async def revoke_all_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> RevokeSessionsResponse:
    """Revoke all sessions except current one."""
    current_session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if not current_session_id:
        raise HTTPException(status_code=400, detail="Текущая сессия не определена")

    count = await session_service.revoke_all_except_current(current_user.id, current_session_id)

    logger.info(f"User {current_user.id} revoked {count} sessions (kept current)")

    return RevokeSessionsResponse(revoked_count=count, message=f"Завершено сессий: {count}")
