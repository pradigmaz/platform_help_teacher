"""
Session management service.
Tracks active sessions per user and allows revocation.
"""

import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from app.core.config import settings
from app.core.redis import get_redis
from app.fingerprint_contract import build_session_device_summary

logger = logging.getLogger(__name__)

SESSION_PREFIX = "session:"
USER_SESSIONS_PREFIX = "user_sessions:"
SESSION_TTL = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

# Lua script for atomic session cleanup
CLEANUP_OLD_SESSIONS_SCRIPT = """
local user_sessions_key = KEYS[1]
local session_prefix = ARGV[1]
local max_sessions = tonumber(ARGV[2])

-- Get all session IDs for user
local session_ids = redis.call('SMEMBERS', user_sessions_key)

-- Build list of valid sessions with their created_at timestamps
local valid_sessions = {}
for _, sid in ipairs(session_ids) do
    local session_key = session_prefix .. sid
    local data = redis.call('GET', session_key)

    if data then
        local parsed = cjson.decode(data)
        -- Skip impersonation sessions from count
        if not parsed.is_impersonation then
            table.insert(valid_sessions, {
                id = sid,
                created_at = parsed.created_at or ""
            })
        end
    else
        -- Expired session, remove from set
        redis.call('SREM', user_sessions_key, sid)
    end
end

-- Sort by created_at (oldest first)
table.sort(valid_sessions, function(a, b)
    return a.created_at < b.created_at
end)

-- Calculate how many to remove
local sessions_to_remove = #valid_sessions - max_sessions + 1
local removed_count = 0

if sessions_to_remove > 0 then
    for i = 1, sessions_to_remove do
        local sid = valid_sessions[i].id
        local session_key = session_prefix .. sid

        -- Delete session data
        redis.call('DEL', session_key)
        -- Remove from user's session set
        redis.call('SREM', user_sessions_key, sid)

        removed_count = removed_count + 1
    end
end

return removed_count
"""


def _build_device_summary(device_fingerprint: str | None) -> dict[str, object] | None:
    return build_session_device_summary(device_fingerprint)


def _mask_ip_for_storage(ip_address: str | None) -> str | None:
    if not ip_address:
        return None
    parts = ip_address.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.x.x"
    return ip_address[:8] + "..."


async def create_session(
    user_id: UUID,
    session_id: str,
    device_fingerprint: str | None = None,
    ip_address: str | None = None,
    is_impersonation: bool = False,
) -> bool:
    """
    Create a new session for user.
    Enforces MAX_ACTIVE_SESSIONS limit by removing oldest sessions atomically.

    Args:
        is_impersonation: If True, don't count against user's session limit
                         (admin impersonating student shouldn't kick student out)

    Returns True if session created successfully.
    """
    redis = await get_redis()
    user_id_str = str(user_id)
    device_summary = _build_device_summary(device_fingerprint)

    session_data = json.dumps(
        {
            "user_id": user_id_str,
            "created_at": datetime.now(UTC).isoformat(),
            "device_summary": device_summary,
            "ip_address": _mask_ip_for_storage(ip_address),
            "is_impersonation": is_impersonation,
        }
    )

    user_sessions_key = f"{USER_SESSIONS_PREFIX}{user_id_str}"

    if is_impersonation:
        session_key = f"{SESSION_PREFIX}{session_id}"
        await redis.setex(session_key, SESSION_TTL, session_data)
        await redis.sadd(user_sessions_key, session_id)
        await redis.expire(user_sessions_key, SESSION_TTL)
        logger.info(
            f"[SessionService:create_session] Created impersonation session {session_id[:8]}... for user {user_id_str}"
        )
        return True

    try:
        removed_count = await redis.eval(
            CLEANUP_OLD_SESSIONS_SCRIPT,
            1,  # number of keys
            user_sessions_key,  # KEYS[1]
            SESSION_PREFIX,  # ARGV[1]
            settings.MAX_ACTIVE_SESSIONS,  # ARGV[2]
        )

        if removed_count > 0:
            logger.info(
                f"[SessionService:create_session] Atomically removed {removed_count} old session(s) for user {user_id_str}"
            )
    except Exception as e:
        logger.error(f"[SessionService:create_session] Error cleaning old sessions for user {user_id_str}: {e}")
        # Continue with session creation even if cleanup fails

    session_key = f"{SESSION_PREFIX}{session_id}"
    await redis.setex(session_key, SESSION_TTL, session_data)
    await redis.sadd(user_sessions_key, session_id)
    await redis.expire(user_sessions_key, SESSION_TTL)

    logger.info(f"[SessionService:create_session] Created session {session_id[:8]}... for user {user_id_str}")
    return True


async def validate_session(session_id: str, expected_user_id: str | UUID | None = None) -> dict | None:
    """
    Validate session exists and is not revoked.
    Returns session data if valid, None otherwise.
    """
    redis = await get_redis()
    session_key = f"{SESSION_PREFIX}{session_id}"

    data = await redis.get(session_key)
    if not data:
        logger.debug(f"[SessionService:validate_session] Session {session_id[:8]}... not found")
        return None

    try:
        session_data = json.loads(data)
        if not isinstance(session_data, dict):
            logger.error(f"[SessionService:validate_session] Session {session_id[:8]}... payload is not an object")
            return None

        if expected_user_id is not None:
            actual_user_id = session_data.get("user_id")
            expected_user_id_str = str(expected_user_id)
            if actual_user_id != expected_user_id_str:
                logger.warning(
                    "[SessionService:validate_session] Session %s... owner mismatch: expected=%s actual=%s",
                    session_id[:8],
                    expected_user_id_str,
                    actual_user_id,
                )
                return None

        logger.debug(
            f"[SessionService:validate_session] Session {session_id[:8]}... validated for user {session_data.get('user_id')}"
        )
        return session_data
    except json.JSONDecodeError:
        logger.error(f"[SessionService:validate_session] Failed to decode session data for {session_id[:8]}...")
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
                logger.info(f"[SessionService:revoke_session] Revoked session {session_id[:8]}... for user {user_id}")
        except json.JSONDecodeError:
            logger.error(f"[SessionService:revoke_session] Failed to decode session data for {session_id[:8]}...")

    deleted = await redis.delete(session_key)
    return deleted > 0


async def revoke_all_user_sessions(user_id: UUID) -> int:
    """Revoke all sessions for a user. Returns count of revoked sessions."""
    redis = await get_redis()
    user_id_str = str(user_id)
    user_sessions_key = f"{USER_SESSIONS_PREFIX}{user_id_str}"

    sessions = await redis.smembers(user_sessions_key)
    count = 0

    logger.info(f"[SessionService:revoke_all_user_sessions] Revoking {len(sessions)} session(s) for user {user_id_str}")

    for session_id in sessions:
        session_key = f"{SESSION_PREFIX}{session_id}"
        if await redis.delete(session_key):
            count += 1

    await redis.delete(user_sessions_key)

    logger.info(f"[SessionService:revoke_all_user_sessions] Revoked {count} session(s) for user {user_id_str}")
    return count


async def get_user_sessions(user_id: UUID) -> list[dict]:
    """Get all active sessions for a user."""
    redis = await get_redis()
    user_id_str = str(user_id)
    user_sessions_key = f"{USER_SESSIONS_PREFIX}{user_id_str}"

    sessions = await redis.smembers(user_sessions_key)
    result = []

    logger.debug(f"[SessionService:get_user_sessions] Fetching {len(sessions)} session(s) for user {user_id_str}")

    for session_id in sessions:
        session_key = f"{SESSION_PREFIX}{session_id}"
        data = await redis.get(session_key)
        if data:
            try:
                parsed = json.loads(data)
                parsed["session_id"] = session_id
                result.append(parsed)
            except json.JSONDecodeError:
                logger.error(f"[SessionService:get_user_sessions] Failed to decode session {session_id[:8]}...")
        else:
            # Clean up expired session from set
            await redis.srem(user_sessions_key, session_id)
            logger.debug(f"[SessionService:get_user_sessions] Cleaned up expired session {session_id[:8]}...")

    return result


async def revoke_all_except_current(user_id: UUID, current_session_id: str) -> int:
    """Revoke all sessions for a user except the current one."""
    redis = await get_redis()
    user_id_str = str(user_id)
    user_sessions_key = f"{USER_SESSIONS_PREFIX}{user_id_str}"

    sessions = await redis.smembers(user_sessions_key)
    count = 0

    logger.info(
        f"[SessionService:revoke_all_except_current] Revoking sessions for user {user_id_str}, keeping {current_session_id[:8]}..."
    )

    for session_id in sessions:
        if session_id == current_session_id:
            continue
        session_key = f"{SESSION_PREFIX}{session_id}"
        if await redis.delete(session_key):
            await redis.srem(user_sessions_key, session_id)
            count += 1

    logger.info(f"[SessionService:revoke_all_except_current] Revoked {count} session(s) for user {user_id_str}")
    return count


async def get_session_owner(session_id: str) -> str | None:
    """Get user_id for a session. Returns None if session doesn't exist."""
    redis = await get_redis()
    session_key = f"{SESSION_PREFIX}{session_id}"
    data = await redis.get(session_key)

    if not data:
        logger.debug(f"[SessionService:get_session_owner] Session {session_id[:8]}... not found")
        return None

    try:
        parsed = json.loads(data)
        user_id = parsed.get("user_id")
        logger.debug(f"[SessionService:get_session_owner] Session {session_id[:8]}... belongs to user {user_id}")
        return user_id
    except json.JSONDecodeError:
        logger.error(f"[SessionService:get_session_owner] Failed to decode session data for {session_id[:8]}...")
        return None
