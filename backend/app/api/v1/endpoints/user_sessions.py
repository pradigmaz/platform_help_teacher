"""User session management endpoints."""
import json
import logging
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_current_user
from app.audit import audit_action, ActionType, EntityType
from app.audit.middleware import SESSION_COOKIE_NAME
from app.core.config import settings
from app.core.limiter import limiter
from app.models import User
from app.schemas.session import (
    SessionResponse, SessionListResponse, RevokeSessionsResponse, DeviceInfo
)
from app.services import session_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _parse_device_info(fingerprint_str: Optional[str]) -> DeviceInfo:
    """Parse device info from fingerprint JSON string."""
    if not fingerprint_str:
        return DeviceInfo()
    
    try:
        fp = json.loads(fingerprint_str)
    except (json.JSONDecodeError, TypeError):
        return DeviceInfo()
    
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
    
    return DeviceInfo(platform=platform, browser=browser, screen=screen)


def _mask_ip(ip: Optional[str]) -> Optional[str]:
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
        
        sessions.append(SessionResponse(
            session_id=session_id,
            created_at=created_at,
            ip_address=_mask_ip(s.get("ip_address")),
            device=_parse_device_info(s.get("device_fingerprint")),
            is_current=(session_id == current_session_id),
        ))
    
    # Sort: current first, then by created_at desc
    sessions.sort(key=lambda x: (not x.is_current, x.created_at), reverse=True)
    
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
        raise HTTPException(
            status_code=400,
            detail="Нельзя завершить текущую сессию. Используйте выход из аккаунта."
        )
    
    # Check ownership
    owner_id = await session_service.get_session_owner(session_id)
    if owner_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    success = await session_service.revoke_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    logger.info(f"User {current_user.id} revoked session {session_id[:8]}...")
    
    return RevokeSessionsResponse(
        revoked_count=1,
        message="Сессия завершена"
    )


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
    
    count = await session_service.revoke_all_except_current(
        current_user.id, 
        current_session_id
    )
    
    logger.info(f"User {current_user.id} revoked {count} sessions (kept current)")
    
    return RevokeSessionsResponse(
        revoked_count=count,
        message=f"Завершено сессий: {count}"
    )
