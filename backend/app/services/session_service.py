"""
Session management service.
Tracks active sessions per user and allows revocation.
"""
import json
import logging
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from app.core.redis import get_redis
from app.core.config import settings

logger = logging.getLogger(__name__)

SESSION_PREFIX = "session:"
USER_SESSIONS_PREFIX = "user_sessions:"
SESSION_TTL = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


async def create_session(
    user_id: UUID,
    session_id: str,
    device_fingerprint: Optional[str] = None,
    ip_address: Optional[str] = None,
    is_impersonation: bool = False,
) -> bool:
    """
    Create a new session for user.
    Enforces MAX_ACTIVE_SESSIONS limit by removing oldest sessions.
    
    Args:
        is_impersonation: If True, don't count against user's session limit
                         (admin impersonating student shouldn't kick student out)
    
    Returns True if session created successfully.
    """
    redis = await get_redis()
    user_id_str = str(user_id)
    
    session_data = json.dumps({
        "user_id": user_id_str,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "device_fingerprint": device_fingerprint,
        "ip_address": ip_address,
        "is_impersonation": is_impersonation,
    })
    
    # Impersonation sessions don't count against limit
    if is_impersonation:
        session_key = f"{SESSION_PREFIX}{session_id}"
        await redis.setex(session_key, SESSION_TTL, session_data)
        logger.info(f"Created impersonation session {session_id[:8]}... for user {user_id_str}")
        return True
    
    # Add session to user's session set
    user_sessions_key = f"{USER_SESSIONS_PREFIX}{user_id_str}"
    
    # Get current sessions count (excluding impersonation sessions)
    current_sessions = await redis.smembers(user_sessions_key)
    real_sessions = []
    
    for sid in current_sessions:
        session_key = f"{SESSION_PREFIX}{sid}"
        data = await redis.get(session_key)
        if data:
            try:
                parsed = json.loads(data)
                # Skip impersonation sessions from count
                if not parsed.get("is_impersonation", False):
                    real_sessions.append((sid, parsed.get("created_at", "")))
            except json.JSONDecodeError:
                real_sessions.append((sid, ""))
        else:
            # Expired session, remove from set
            await redis.srem(user_sessions_key, sid)
    
    # If at limit, remove oldest non-impersonation sessions
    if len(real_sessions) >= settings.MAX_ACTIVE_SESSIONS:
        real_sessions.sort(key=lambda x: x[1])
        sessions_to_remove = len(real_sessions) - settings.MAX_ACTIVE_SESSIONS + 1
        
        for sid, _ in real_sessions[:sessions_to_remove]:
            await revoke_session(session_id=sid)
            logger.info(f"Removed old session {sid[:8]}... for user {user_id_str}")
    
    # Create new session
    session_key = f"{SESSION_PREFIX}{session_id}"
    await redis.setex(session_key, SESSION_TTL, session_data)
    await redis.sadd(user_sessions_key, session_id)
    await redis.expire(user_sessions_key, SESSION_TTL)
    
    logger.info(f"Created session {session_id[:8]}... for user {user_id_str}")
    return True


async def validate_session(session_id: str) -> Optional[dict]:
    """
    Validate session exists and is not revoked.
    Returns session data if valid, None otherwise.
    """
    redis = await get_redis()
    session_key = f"{SESSION_PREFIX}{session_id}"
    
    data = await redis.get(session_key)
    if not data:
        return None
    
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


async def revoke_session(session_id: str) -> bool:
    """Revoke a specific session."""
    redis = await get_redis()
    session_key = f"{SESSION_PREFIX}{session_id}"
    
    # Get session data to find user_id
    data = await redis.get(session_key)
    if data:
        try:
            parsed = json.loads(data)
            user_id = parsed.get("user_id")
            if user_id:
                user_sessions_key = f"{USER_SESSIONS_PREFIX}{user_id}"
                await redis.srem(user_sessions_key, session_id)
        except json.JSONDecodeError:
            pass
    
    deleted = await redis.delete(session_key)
    return deleted > 0


async def revoke_all_user_sessions(user_id: UUID) -> int:
    """Revoke all sessions for a user. Returns count of revoked sessions."""
    redis = await get_redis()
    user_id_str = str(user_id)
    user_sessions_key = f"{USER_SESSIONS_PREFIX}{user_id_str}"
    
    sessions = await redis.smembers(user_sessions_key)
    count = 0
    
    for session_id in sessions:
        session_key = f"{SESSION_PREFIX}{session_id}"
        if await redis.delete(session_key):
            count += 1
    
    await redis.delete(user_sessions_key)
    
    logger.info(f"Revoked {count} sessions for user {user_id_str}")
    return count


async def get_user_sessions(user_id: UUID) -> list[dict]:
    """Get all active sessions for a user."""
    redis = await get_redis()
    user_id_str = str(user_id)
    user_sessions_key = f"{USER_SESSIONS_PREFIX}{user_id_str}"
    
    sessions = await redis.smembers(user_sessions_key)
    result = []
    
    for session_id in sessions:
        session_key = f"{SESSION_PREFIX}{session_id}"
        data = await redis.get(session_key)
        if data:
            try:
                parsed = json.loads(data)
                parsed["session_id"] = session_id
                result.append(parsed)
            except json.JSONDecodeError:
                pass
        else:
            # Clean up expired session from set
            await redis.srem(user_sessions_key, session_id)
    
    return result


async def revoke_all_except_current(user_id: UUID, current_session_id: str) -> int:
    """Revoke all sessions for a user except the current one."""
    redis = await get_redis()
    user_id_str = str(user_id)
    user_sessions_key = f"{USER_SESSIONS_PREFIX}{user_id_str}"
    
    sessions = await redis.smembers(user_sessions_key)
    count = 0
    
    for session_id in sessions:
        if session_id == current_session_id:
            continue
        session_key = f"{SESSION_PREFIX}{session_id}"
        if await redis.delete(session_key):
            await redis.srem(user_sessions_key, session_id)
            count += 1
    
    logger.info(f"Revoked {count} sessions for user {user_id_str} (kept current: {current_session_id[:8]}...)")
    return count


async def get_session_owner(session_id: str) -> Optional[str]:
    """Get user_id for a session. Returns None if session doesn't exist."""
    redis = await get_redis()
    session_key = f"{SESSION_PREFIX}{session_id}"
    data = await redis.get(session_key)
    
    if not data:
        return None
    
    try:
        parsed = json.loads(data)
        return parsed.get("user_id")
    except json.JSONDecodeError:
        return None
