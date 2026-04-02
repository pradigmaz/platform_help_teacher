from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.deps import get_current_active_superuser
from app.api.v1.endpoints.backup.deps import get_restore_service
from app.api.v1.endpoints.backup.restore import router
from app.models import User, UserRole
from tests.support.http import router_client

pytestmark = pytest.mark.smoke


def make_admin() -> User:
    return User(
        id=uuid4(),
        full_name="Smoke Admin",
        username="smoke-admin",
        role=UserRole.ADMIN,
        is_active=True,
        onboarding_completed=True,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_restore_requires_exact_confirmation():
    service = SimpleNamespace()

    async def override_admin() -> User:
        return make_admin()

    async def override_service():
        return service

    async with router_client(
        router,
        dependency_overrides={
            get_current_active_superuser: override_admin,
            get_restore_service: override_service,
        },
    ) as client:
        response = await client.post(
            "/demo_backup.enc/restore",
            json={
                "drop_existing": False,
                "confirmation": "RESTORE-wrong.enc",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid confirmation. Expected: 'RESTORE-demo_backup.enc'"


@pytest.mark.asyncio
async def test_restore_returns_service_payload():
    restore_result = SimpleNamespace(
        success=True,
        status="restored",
        error=None,
        format_version=2,
        portable=True,
        created_with_current_key=True,
        offsite_used=False,
    )

    class RestoreStub:
        async def restore_backup(self, backup_key: str, drop_existing: bool, recovery_code: str | None):
            assert backup_key == "demo_backup.enc"
            assert drop_existing is True
            assert recovery_code == "ABCDEFGHIJKLMNOP"
            return restore_result

    async def override_admin() -> User:
        return make_admin()

    async def override_service():
        return RestoreStub()

    async with router_client(
        router,
        dependency_overrides={
            get_current_active_superuser: override_admin,
            get_restore_service: override_service,
        },
    ) as client:
        response = await client.post(
            "/demo_backup.enc/restore",
            json={
                "drop_existing": True,
                "recovery_code": "ABCDEFGHIJKLMNOP",
                "confirmation": "RESTORE-demo_backup.enc",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "status": "restored",
        "error": None,
        "format_version": 2,
        "portable": True,
        "created_with_current_key": True,
        "offsite_used": False,
    }


@pytest.mark.asyncio
async def test_verify_returns_service_payload():
    verify_result = SimpleNamespace(
        valid=True,
        status="verified",
        error=None,
        format_version=2,
        portable=False,
        created_with_current_key=True,
        offsite_used=True,
    )

    class RestoreStub:
        async def verify_backup(self, backup_key: str, recovery_code: str | None):
            assert backup_key == "demo_backup.enc"
            assert recovery_code == "ABCDEFGHIJKLMNOP"
            return verify_result

    async def override_admin() -> User:
        return make_admin()

    async def override_service():
        return RestoreStub()

    async with router_client(
        router,
        dependency_overrides={
            get_current_active_superuser: override_admin,
            get_restore_service: override_service,
        },
    ) as client:
        response = await client.post(
            "/demo_backup.enc/verify",
            json={"recovery_code": "ABCDEFGHIJKLMNOP"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "valid": True,
        "backup_key": "demo_backup.enc",
        "status": "verified",
        "error": None,
        "format_version": 2,
        "portable": False,
        "created_with_current_key": True,
        "offsite_used": True,
    }
