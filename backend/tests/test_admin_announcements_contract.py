from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.api.deps import get_current_teacher, get_current_user, get_db
from app.api.v1.endpoints.admin_announcements import router as admin_router
from app.api.v1.endpoints.student.notifications import router as student_router
from app.models.announcement import AnnouncementSendStatus
from app.models.user import User, UserRole
from tests.support.http import router_client


def make_user(role: UserRole) -> User:
    return User(
        id=uuid4(),
        full_name=f"{role.value.title()} User",
        username=role.value,
        role=role,
        is_active=True,
        onboarding_completed=True,
        created_at=datetime.now(UTC),
    )


def make_announcement(
    *,
    is_draft: bool = True,
    send_status: AnnouncementSendStatus = AnnouncementSendStatus.NOT_SENT,
) -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid4(),
        title="Обновление платформы",
        content="Подробности обновления",
        created_by=uuid4(),
        author=SimpleNamespace(full_name="Главный преподаватель"),
        is_draft=is_draft,
        send_status=send_status,
        published_at=None if is_draft else now,
        send_started_at=None,
        sent_at=None,
        sent_by=None,
        created_at=now,
        updated_at=now,
        delivery_stats=None,
        delivery_error=None,
    )


def test_announcement_send_status_orm_uses_lowercase_db_values():
    from app.models.announcement import ANNOUNCEMENT_SEND_STATUS_DB_VALUES, Announcement

    enum_type = Announcement.__table__.c.send_status.type

    assert enum_type.enums == ANNOUNCEMENT_SEND_STATUS_DB_VALUES


@pytest.mark.asyncio
async def test_admin_announcements_list_allows_teacher_and_returns_author_name():
    db = AsyncMock()
    teacher = make_user(UserRole.TEACHER)
    announcement = make_announcement(is_draft=False)

    async def override_teacher() -> User:
        return teacher

    async def override_db():
        return db

    with patch(
        "app.api.v1.endpoints.admin_announcements.crud_announcement.get_all",
        new=AsyncMock(return_value=[announcement]),
    ):
        async with router_client(
            (admin_router, "/admin/announcements"),
            dependency_overrides={get_current_teacher: override_teacher, get_db: override_db},
        ) as client:
            response = await client.get("/admin/announcements/")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["author_name"] == "Главный преподаватель"
    assert payload[0]["send_status"] == AnnouncementSendStatus.NOT_SENT.value


@pytest.mark.asyncio
async def test_admin_announcements_reject_student_access():
    db = AsyncMock()
    student = make_user(UserRole.STUDENT)

    async def override_user() -> User:
        return student

    async def override_db():
        return db

    async with router_client(
        (admin_router, "/admin/announcements"),
        dependency_overrides={get_current_user: override_user, get_db: override_db},
    ) as client:
        response = await client.get("/admin/announcements/")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_sent_announcement_cannot_be_edited():
    db = AsyncMock()
    teacher = make_user(UserRole.TEACHER)
    announcement = make_announcement(is_draft=False, send_status=AnnouncementSendStatus.SENT)

    async def override_teacher() -> User:
        return teacher

    async def override_db():
        return db

    with patch(
        "app.api.v1.endpoints.admin_announcements.crud_announcement.get",
        new=AsyncMock(return_value=announcement),
    ):
        async with router_client(
            (admin_router, "/admin/announcements"),
            dependency_overrides={get_current_teacher: override_teacher, get_db: override_db},
        ) as client:
            response = await client.put(
                f"/admin/announcements/{announcement.id}",
                json={"title": "Новое", "content": "Новое содержимое для объявления"},
            )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_only_drafts_can_be_deleted():
    db = AsyncMock()
    teacher = make_user(UserRole.TEACHER)
    announcement = make_announcement(is_draft=False)

    async def override_teacher() -> User:
        return teacher

    async def override_db():
        return db

    with patch(
        "app.api.v1.endpoints.admin_announcements.crud_announcement.get",
        new=AsyncMock(return_value=announcement),
    ):
        async with router_client(
            (admin_router, "/admin/announcements"),
            dependency_overrides={get_current_teacher: override_teacher, get_db: override_db},
        ) as client:
            response = await client.delete(f"/admin/announcements/{announcement.id}")

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_send_enqueues_delivery_and_returns_accepted():
    db = AsyncMock()
    teacher = make_user(UserRole.TEACHER)
    announcement = make_announcement(is_draft=False, send_status=AnnouncementSendStatus.NOT_SENT)
    queued = make_announcement(is_draft=False, send_status=AnnouncementSendStatus.SENDING)
    queued.id = announcement.id
    queued.created_by = announcement.created_by
    queued.author = announcement.author
    queued.published_at = announcement.published_at

    async def override_teacher() -> User:
        return teacher

    async def override_db():
        return db

    with (
        patch(
            "app.api.v1.endpoints.admin_announcements.crud_announcement.get",
            new=AsyncMock(return_value=announcement),
        ),
        patch(
            "app.api.v1.endpoints.admin_announcements.crud_announcement.mark_send_enqueued",
            new=AsyncMock(return_value=queued),
        ),
        patch("app.api.v1.endpoints.admin_announcements.send_announcement_task.delay") as delay_mock,
    ):
        async with router_client(
            (admin_router, "/admin/announcements"),
            dependency_overrides={get_current_teacher: override_teacher, get_db: override_db},
        ) as client:
            response = await client.post(f"/admin/announcements/{announcement.id}/send")

    assert response.status_code == 202
    assert response.json()["send_status"] == AnnouncementSendStatus.SENDING.value
    delay_mock.assert_called_once_with(str(announcement.id))


@pytest.mark.asyncio
async def test_student_announcements_respect_web_channel_toggle():
    db = AsyncMock()
    student = make_user(UserRole.STUDENT)

    async def override_user() -> User:
        return student

    async def override_db():
        return db

    with (
        patch(
            "app.api.v1.endpoints.student.notifications.crud_notification_settings.get_or_create",
            new=AsyncMock(
                return_value=SimpleNamespace(channel_web=False, notify_announcements=True),
            ),
        ),
        patch(
            "app.api.v1.endpoints.student.notifications.crud_announcement.get_published",
            new=AsyncMock(),
        ) as get_published_mock,
    ):
        async with router_client(
            (student_router, "/student"),
            dependency_overrides={get_current_user: override_user, get_db: override_db},
        ) as client:
            response = await client.get("/student/announcements")

    assert response.status_code == 200
    assert response.json() == []
    get_published_mock.assert_not_called()
