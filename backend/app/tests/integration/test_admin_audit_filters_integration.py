from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.api.deps import get_current_active_superuser, get_db
from app.api.v1.endpoints.admin_audit import router
from app.audit.models import StudentAuditLog
from app.db.session import AsyncSessionLocal
from app.models import User, UserRole
from tests.support.http import router_client

pytestmark = pytest.mark.integration


def make_user(*, suffix: str, role: UserRole) -> User:
    return User(
        id=uuid4(),
        full_name=f"{role.value.title()} {suffix}",
        username=f"{role.value}_{suffix}",
        role=role,
        is_active=True,
    )


def make_audit_log(
    *,
    user_id,
    action_type: str,
    response_status: int,
    ip_address: str,
    path: str,
    created_at: datetime,
) -> StudentAuditLog:
    return StudentAuditLog(
        user_id=user_id,
        actor_role="student",
        action_type=action_type,
        entity_type="session",
        entity_id=None,
        method="POST",
        path=path,
        response_status=response_status,
        duration_ms=25,
        ip_address=ip_address,
        ip_forwarded=None,
        user_agent="pytest",
        fingerprint=None,
        created_at=created_at,
    )


@pytest.mark.asyncio
async def test_get_audit_logs_applies_sql_filters_and_pagination():
    suffix = uuid4().hex[:8]
    now = datetime.now(UTC)

    async with AsyncSessionLocal() as session, session.begin():
        admin = make_user(suffix=f"admin_{suffix}", role=UserRole.ADMIN)
        student = make_user(suffix=f"student_{suffix}", role=UserRole.STUDENT)
        admin_view = User(
            id=admin.id,
            full_name=admin.full_name,
            username=admin.username,
            role=admin.role,
            is_active=True,
        )
        session.add_all(
            [
                admin,
                student,
                make_audit_log(
                    user_id=student.id,
                    action_type="AUTH_LOGIN",
                    response_status=401,
                    ip_address="10.20.30.40",
                    path="/api/v1/auth/otp",
                    created_at=now,
                ),
                make_audit_log(
                    user_id=student.id,
                    action_type="AUTH_LOGOUT",
                    response_status=200,
                    ip_address="10.20.30.40",
                    path="/api/v1/auth/logout",
                    created_at=now,
                ),
                make_audit_log(
                    user_id=None,
                    action_type="AUTH_LOGIN",
                    response_status=401,
                    ip_address="192.168.1.10",
                    path="/api/v1/student/profile",
                    created_at=now - timedelta(days=5),
                ),
            ]
        )
        await session.flush()

        async def override_admin() -> User:
            return admin_view

        async def override_db():
            return session

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
                response = await client.get(
                    "/audit",
                    params={
                        "user_id": str(student.id),
                        "action_type": "AUTH_LOGIN",
                        "ip_address": "10.20.30",
                        "path_contains": "/auth",
                        "date_from": (now - timedelta(minutes=1)).isoformat(),
                        "date_to": (now + timedelta(minutes=1)).isoformat(),
                        "skip": 0,
                        "limit": 10,
                    },
                )

        payload = response.json()
        assert response.status_code == 200
        assert payload["total"] == 1
        assert payload["skip"] == 0
        assert payload["limit"] == 10
        assert len(payload["items"]) == 1
        assert payload["items"][0]["action_type"] == "AUTH_LOGIN"
        assert payload["items"][0]["path"] == "/api/v1/auth/otp"
        assert payload["items"][0]["user_name"] == student.full_name

        await session.rollback()


@pytest.mark.asyncio
async def test_preview_and_clear_use_same_real_db_filters():
    suffix = uuid4().hex[:8]
    now = datetime.now(UTC)

    async with AsyncSessionLocal() as session:
        admin = make_user(suffix=f"admin_{suffix}", role=UserRole.ADMIN)
        admin_view = User(
            id=admin.id,
            full_name=admin.full_name,
            username=admin.username,
            role=admin.role,
            is_active=True,
        )
        session.add(admin)
        await session.flush()

        remaining_log = make_audit_log(
            user_id=None,
            action_type="PROFILE_VIEW",
            response_status=200,
            ip_address="127.0.0.1",
            path="/api/v1/student/profile",
            created_at=now,
        )
        deleted_logs = [
            make_audit_log(
                user_id=None,
                action_type="AUTH_LOGIN",
                response_status=401,
                ip_address="127.0.0.2",
                path="/api/v1/auth/otp",
                created_at=now,
            ),
            make_audit_log(
                user_id=None,
                action_type="AUTH_LOGIN",
                response_status=500,
                ip_address="127.0.0.3",
                path="/api/v1/auth/otp",
                created_at=now,
            ),
        ]
        session.add_all([remaining_log, *deleted_logs])
        await session.commit()

        async def override_admin() -> User:
            return admin_view

        async def override_db():
            return session

        async with router_client(
            (router, "/audit"),
            dependency_overrides={
                get_current_active_superuser: override_admin,
                get_db: override_db,
            },
        ) as client:
            preview_response = await client.get(
                "/audit/clear/preview",
                params={"action_type": "AUTH_LOGIN", "status_codes": "401,500"},
            )
            clear_response = await client.delete(
                "/audit/clear",
                params={"action_type": "AUTH_LOGIN", "status_codes": "401,500", "confirm": "true"},
            )

        assert preview_response.status_code == 200
        assert preview_response.json()["count"] == 2
        assert preview_response.json()["by_status"] == {"401": 1, "500": 1}

        assert clear_response.status_code == 200
        assert clear_response.json()["deleted"] == 2

        remaining = (
            (
                await session.execute(
                    select(StudentAuditLog).where(
                        StudentAuditLog.id.in_([remaining_log.id, *(log.id for log in deleted_logs)])
                    )
                )
            )
            .scalars()
            .all()
        )
        remaining_by_id = {log.id: log for log in remaining}
        assert remaining_log.id in remaining_by_id
        assert deleted_logs[0].id not in remaining_by_id
        assert deleted_logs[1].id not in remaining_by_id

        await session.delete(remaining_log)
        await session.delete(admin)
        await session.commit()
