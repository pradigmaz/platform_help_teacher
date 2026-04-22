from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.api.deps import get_current_user
from app.api.v1.endpoints.admin_exam_banks import router as admin_exam_banks_router
from app.api.v1.endpoints.admin_subject_offerings import router as admin_subjects_router
from app.db.session import get_db as session_get_db
from app.models.group_subject_offering import FinalControlType
from app.models.user import User, UserRole
from app.services.attestation.lab_count_sync import DEFAULT_TOTAL_LABS_COUNT
from tests.support.http import router_client


def make_user(role: UserRole) -> User:
    return User(
        id=uuid4(),
        full_name=f"{role.value.title()} Тестов",
        username=f"{role.value}_test",
        role=role,
        is_active=True,
    )


def make_offering(final_control_type: FinalControlType) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        group_id=uuid4(),
        subject_id=uuid4(),
        semester="2099-1",
        final_control_type=final_control_type,
        group=SimpleNamespace(name="ИС-101"),
        subject=SimpleNamespace(name="Компьютерные сети"),
        exam_question_bank_id=None,
    )


async def override_db():
    return AsyncMock()


@pytest.mark.asyncio
async def test_teacher_cannot_read_admin_subject_offerings():
    teacher = make_user(UserRole.TEACHER)

    async def override_user() -> User:
        return teacher

    async with router_client(
        (admin_subjects_router, "/admin/subjects"),
        dependency_overrides={
            get_current_user: override_user,
            session_get_db: override_db,
        },
    ) as client:
        response = await client.get("/admin/subjects/offerings", params={"semester": "2099-1"})

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_teacher_cannot_read_exam_bank_groups():
    teacher = make_user(UserRole.TEACHER)

    async def override_user() -> User:
        return teacher

    async with router_client(
        (admin_exam_banks_router, "/admin/exams"),
        dependency_overrides={
            get_current_user: override_user,
            session_get_db: override_db,
        },
    ) as client:
        response = await client.get("/admin/exams/groups")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_non_exam_offering_rejected_for_automatic_queue():
    admin = make_user(UserRole.ADMIN)
    offering = make_offering(FinalControlType.CREDIT)

    async def override_user() -> User:
        return admin

    with patch(
        "app.api.v1.endpoints.admin_subject_offerings._get_offering_or_404",
        new=AsyncMock(return_value=offering),
    ):
        async with router_client(
            (admin_subjects_router, "/admin/subjects"),
            dependency_overrides={
                get_current_user: override_user,
                session_get_db: override_db,
            },
        ) as client:
            response = await client.get(f"/admin/subjects/offerings/{offering.id}/automatic-queue")

    assert response.status_code == 400
    assert "экзаменационной" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_non_exam_offering_rejected_for_automatic_refusal_mutation():
    admin = make_user(UserRole.ADMIN)
    offering = make_offering(FinalControlType.CREDIT)
    db = SimpleNamespace(commit=AsyncMock(), get=AsyncMock())
    upsert_refusal = AsyncMock()

    async def override_user() -> User:
        return admin

    async def override_subjects_db():
        return db

    with (
        patch(
            "app.api.v1.endpoints.admin_subject_offerings._get_offering_or_404",
            new=AsyncMock(return_value=offering),
        ),
        patch(
            "app.api.v1.endpoints.admin_subject_offerings.upsert_automatic_pass_refusal",
            new=upsert_refusal,
        ),
    ):
        async with router_client(
            (admin_subjects_router, "/admin/subjects"),
            dependency_overrides={
                get_current_user: override_user,
                session_get_db: override_subjects_db,
            },
        ) as client:
            response = await client.post(
                f"/admin/subjects/offerings/{offering.id}/automatic-refusals/{uuid4()}",
                json={"reason": "manual check"},
            )

    assert response.status_code == 400
    upsert_refusal.assert_not_awaited()
    db.commit.assert_not_awaited()
    db.get.assert_not_awaited()


@pytest.mark.asyncio
async def test_disabled_automatic_settings_block_refusal_mutation():
    admin = make_user(UserRole.ADMIN)
    offering = make_offering(FinalControlType.EXAM)
    db = SimpleNamespace(commit=AsyncMock(), get=AsyncMock())
    upsert_refusal = AsyncMock()
    disabled_settings = SimpleNamespace(automatic_enabled=False, automatic_places=3, labs_count=7)

    async def override_user() -> User:
        return admin

    async def override_subjects_db():
        return db

    with (
        patch(
            "app.api.v1.endpoints.admin_subject_offerings._get_offering_or_404",
            new=AsyncMock(return_value=offering),
        ),
        patch(
            "app.api.v1.endpoints.admin_subject_offerings.lab_settings_service.get_lab_settings",
            new=AsyncMock(return_value=disabled_settings),
        ),
        patch(
            "app.api.v1.endpoints.admin_subject_offerings.upsert_automatic_pass_refusal",
            new=upsert_refusal,
        ),
    ):
        async with router_client(
            (admin_subjects_router, "/admin/subjects"),
            dependency_overrides={
                get_current_user: override_user,
                session_get_db: override_subjects_db,
            },
        ) as client:
            response = await client.post(
                f"/admin/subjects/offerings/{offering.id}/automatic-refusals/{uuid4()}",
                json={"reason": "manual check"},
            )

    assert response.status_code == 400
    assert "автоматы отключены" in response.json()["detail"].lower()
    upsert_refusal.assert_not_awaited()
    db.commit.assert_not_awaited()
    db.get.assert_not_awaited()


@pytest.mark.asyncio
async def test_automatic_queue_uses_global_defaults_when_lab_settings_missing():
    admin = make_user(UserRole.ADMIN)
    offering = make_offering(FinalControlType.EXAM)
    queue_entry = SimpleNamespace(
        student_id=uuid4(),
        student_name="Студент Тестов",
        completed_count=DEFAULT_TOTAL_LABS_COUNT,
        automatic_remaining=0,
        completion_at=None,
        queue_position=1,
        is_winner=True,
        is_declined=False,
        declined_reason=None,
    )

    async def override_user() -> User:
        return admin

    with (
        patch(
            "app.api.v1.endpoints.admin_subject_offerings._get_offering_or_404",
            new=AsyncMock(return_value=offering),
        ),
        patch(
            "app.api.v1.endpoints.admin_subject_offerings.lab_settings_service.get_lab_settings",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.api.v1.endpoints.admin_subject_offerings.list_offering_automatic_queue",
            new=AsyncMock(return_value=[queue_entry]),
        ),
    ):
        async with router_client(
            (admin_subjects_router, "/admin/subjects"),
            dependency_overrides={
                get_current_user: override_user,
                session_get_db: override_db,
            },
        ) as client:
            response = await client.get(f"/admin/subjects/offerings/{offering.id}/automatic-queue")

    assert response.status_code == 200
    payload = response.json()
    assert payload["automatic_enabled"] is True
    assert payload["automatic_places"] is None
    assert payload["total_labs"] == DEFAULT_TOTAL_LABS_COUNT
    assert payload["students"][0]["student_name"] == "Студент Тестов"
