"""HTTP-level contract checks for user session endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.deps import get_current_user
from app.api.v1.endpoints.user_sessions import router
from tests.support.http import router_client


class TestUserSessionsHttpContract:
    @pytest.mark.asyncio
    async def test_get_my_sessions_should_allow_60_requests_per_minute_before_429(self):
        mock_user = MagicMock()
        mock_user.id = uuid4()
        request_ip = f"198.51.100.{(uuid4().int % 200) + 1}"

        async def override_user():
            return mock_user

        with patch(
            "app.api.v1.endpoints.user_sessions.session_service.get_user_sessions",
            new=AsyncMock(return_value=[]),
        ):
            async with router_client(
                (router, "/users"),
                dependency_overrides={get_current_user: override_user},
            ) as client:
                headers = {"X-Real-IP": request_ip}
                responses = [await client.get("/users/me/sessions", headers=headers) for _ in range(61)]

        assert all(response.status_code == 200 for response in responses[:60]), (
            f"Counterexample: one of the first 60 responses was not 200 -> "
            f"{[response.status_code for response in responses[:60]]}"
        )
        assert responses[60].status_code == 429, (
            f"Counterexample: 61st response returned {responses[60].status_code} instead of 429"
        )
