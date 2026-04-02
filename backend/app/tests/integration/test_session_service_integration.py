from uuid import uuid4

import pytest

from app.core.redis import get_redis
from app.services import session_service
from tests.support.device_binding import make_fp_json

pytestmark = pytest.mark.integration


async def cleanup_sessions(user_id, *session_ids: str) -> None:
    redis = await get_redis()
    for session_id in session_ids:
        await redis.delete(f"{session_service.SESSION_PREFIX}{session_id}")
    await redis.delete(f"{session_service.USER_SESSIONS_PREFIX}{user_id}")


@pytest.mark.asyncio
async def test_create_validate_and_revoke_session_roundtrip():
    user_id = uuid4()
    session_id = f"it-session-{uuid4().hex}"

    try:
        created = await session_service.create_session(
            user_id,
            session_id,
            device_fingerprint=make_fp_json(),
            ip_address="10.20.30.40",
        )

        assert created is True

        validated = await session_service.validate_session(session_id, expected_user_id=user_id)
        assert validated is not None
        assert validated["user_id"] == str(user_id)
        assert validated["ip_address"] == "10.20.x.x"
        assert validated["device_summary"] is not None
        assert validated["is_impersonation"] is False

        sessions = await session_service.get_user_sessions(user_id)
        assert [session["session_id"] for session in sessions] == [session_id]
        assert await session_service.get_session_owner(session_id) == str(user_id)

        assert await session_service.revoke_session(session_id) is True
        assert await session_service.validate_session(session_id, expected_user_id=user_id) is None
    finally:
        await cleanup_sessions(str(user_id), session_id)


@pytest.mark.asyncio
async def test_revoke_all_except_current_keeps_only_requested_session():
    user_id = uuid4()
    current_session_id = f"it-session-{uuid4().hex}"
    revoked_session_id = f"it-session-{uuid4().hex}"

    try:
        await session_service.create_session(user_id, current_session_id, ip_address="10.20.30.40")
        await session_service.create_session(user_id, revoked_session_id, ip_address="10.20.30.41")

        revoked_count = await session_service.revoke_all_except_current(user_id, current_session_id)

        assert revoked_count == 1
        assert await session_service.validate_session(current_session_id, expected_user_id=user_id) is not None
        assert await session_service.validate_session(revoked_session_id, expected_user_id=user_id) is None

        sessions = await session_service.get_user_sessions(user_id)
        assert [session["session_id"] for session in sessions] == [current_session_id]
    finally:
        await cleanup_sessions(str(user_id), current_session_id, revoked_session_id)
