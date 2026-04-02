from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.deps import get_current_active_superuser, get_db
from app.api.v1.endpoints.admin_audit import router
from app.audit.models import StudentAuditLog
from app.models import User, UserRole
from tests.support.http import router_client

pytestmark = pytest.mark.smoke


def make_admin() -> User:
    return User(
        id=uuid4(),
        full_name="Audit Admin",
        username="audit-admin",
        role=UserRole.ADMIN,
        is_active=True,
        onboarding_completed=True,
        created_at=datetime.now(UTC),
    )


def scalar_result(value):
    result = MagicMock()
    result.scalar.return_value = value
    return result


def rows_result(rows):
    result = MagicMock()
    result.all.return_value = rows
    return result


def logs_result(*logs):
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = list(logs)
    result.scalars.return_value = scalars
    return result


@pytest.mark.asyncio
async def test_preview_rejects_empty_filters():
    db = AsyncMock()

    async def override_admin() -> User:
        return make_admin()

    async def override_db():
        return db

    async with router_client(
        (router, "/audit"),
        dependency_overrides={
            get_current_active_superuser: override_admin,
            get_db: override_db,
        },
    ) as client:
        response = await client.get("/audit/clear/preview")

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one filter is required"


@pytest.mark.asyncio
async def test_preview_returns_count_status_breakdown_and_filter_echo():
    db = AsyncMock()
    db.execute.side_effect = [
        scalar_result(2),
        rows_result([(401, 1), (500, 1)]),
    ]

    async def override_admin() -> User:
        return make_admin()

    async def override_db():
        return db

    async with router_client(
        (router, "/audit"),
        dependency_overrides={
            get_current_active_superuser: override_admin,
            get_db: override_db,
        },
    ) as client:
        response = await client.get(
            "/audit/clear/preview",
            params={"status_codes": "401,500", "action_type": "AUTH_LOGIN"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "count": 2,
        "by_status": {"401": 1, "500": 1},
        "filters": {
            "date_from": None,
            "date_to": None,
            "status_codes": [401, 500],
            "action_type": "AUTH_LOGIN",
        },
    }


@pytest.mark.asyncio
async def test_list_returns_pagination_total_and_items():
    db = AsyncMock()
    log = StudentAuditLog(
        id=uuid4(),
        user_id=None,
        actor_role="student",
        action_type="AUTH_LOGIN",
        entity_type="session",
        entity_id=None,
        method="POST",
        path="/api/v1/auth/otp",
        response_status=200,
        duration_ms=32,
        ip_address="127.0.0.1",
        ip_forwarded=None,
        user_agent="pytest",
        fingerprint=None,
        created_at=datetime.now(UTC),
    )
    db.execute.side_effect = [
        scalar_result(1),
        logs_result(log),
    ]

    async def override_admin() -> User:
        return make_admin()

    async def override_db():
        return db

    async with router_client(
        (router, "/audit"),
        dependency_overrides={
            get_current_active_superuser: override_admin,
            get_db: override_db,
        },
    ) as client:
        with patch(
            "app.api.v1.endpoints.admin_audit.enrich_logs_with_suspicion",
            new=AsyncMock(return_value={}),
        ):
            response = await client.get("/audit", params={"action_type": "AUTH_LOGIN", "skip": 5, "limit": 10})

    payload = response.json()
    assert response.status_code == 200
    assert payload["total"] == 1
    assert payload["skip"] == 5
    assert payload["limit"] == 10
    assert payload["items"][0]["action_type"] == "AUTH_LOGIN"
    assert payload["items"][0]["path"] == "/api/v1/auth/otp"


@pytest.mark.asyncio
async def test_clear_requires_confirmation():
    db = AsyncMock()

    async def override_admin() -> User:
        return make_admin()

    async def override_db():
        return db

    async with router_client(
        (router, "/audit"),
        dependency_overrides={
            get_current_active_superuser: override_admin,
            get_db: override_db,
        },
    ) as client:
        response = await client.delete("/audit/clear", params={"action_type": "AUTH_LOGIN"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Требуется подтверждение (confirm=true)"


@pytest.mark.asyncio
async def test_clear_returns_deleted_count_and_commits():
    db = AsyncMock()
    db.execute.side_effect = [
        scalar_result(2),
        MagicMock(),
    ]
    db.commit = AsyncMock()

    async def override_admin() -> User:
        return make_admin()

    async def override_db():
        return db

    async with router_client(
        (router, "/audit"),
        dependency_overrides={
            get_current_active_superuser: override_admin,
            get_db: override_db,
        },
    ) as client:
        response = await client.delete("/audit/clear", params={"action_type": "AUTH_LOGIN", "confirm": "true"})

    assert response.status_code == 200
    assert response.json()["deleted"] == 2
    assert response.json()["message"] == "Successfully deleted 2 audit logs"
    db.commit.assert_awaited_once()
