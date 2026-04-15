"""HTTP-level contract checks for student dashboard bootstrap."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.deps import get_current_user, get_db
from app.api.v1.endpoints.student.bootstrap import router
from app.models.user import UserRole
from app.schemas.announcement import AnnouncementListResponse
from app.schemas.attestation import AttestationSubjectOption
from tests.support.http import router_client


def make_user(*, group_id=None):
    user = MagicMock()
    user.id = uuid4()
    user.group_id = group_id
    user.full_name = "Иванов Иван Иванович"
    user.username = "ivanov"
    user.telegram_id = None
    user.vk_id = None
    user.role = UserRole.STUDENT
    user.subgroup = 1
    return user


def make_announcement():
    return AnnouncementListResponse(
        id=uuid4(),
        title="Новость",
        content="Контент",
        is_draft=False,
        published_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )


def profile_payload(*, with_group=True):
    return {
        "id": str(uuid4()),
        "full_name": "Иванов Иван Иванович",
        "username": "ivanov",
        "has_telegram": False,
        "has_vk": False,
        "role": "student",
        "group": (
            {
                "id": str(uuid4()),
                "name": "ИТ-11",
                "code": "IT11",
            }
            if with_group
            else None
        ),
    }


def semester_payload():
    return {
        "semester_start_date": "2026-02-01",
        "academic_year": 2025,
        "semester": 2,
    }


def attendance_stats_payload():
    return {
        "total_classes": 10,
        "present": 9,
        "late": 0,
        "excused": 0,
        "absent": 1,
        "attendance_rate": 90.0,
    }


def override_dependencies(user, db):
    async def override_user():
        return user

    async def override_db():
        yield db

    return {get_current_user: override_user, get_db: override_db}


class TestStudentDashboardBootstrapContract:
    @pytest.mark.asyncio
    async def test_happy_path_should_return_bootstrap_payload(self):
        mock_user = make_user(group_id=uuid4())
        mock_db = AsyncMock()
        subject_id = uuid4()

        with (
            patch("app.api.v1.endpoints.student.bootstrap.build_student_profile", new=AsyncMock(return_value=profile_payload())),
            patch(
                "app.api.v1.endpoints.student.bootstrap.load_public_semester_info",
                new=AsyncMock(return_value=semester_payload()),
            ),
            patch(
                "app.api.v1.endpoints.student.bootstrap.list_student_announcements",
                new=AsyncMock(return_value=[make_announcement()]),
            ),
            patch(
                "app.api.v1.endpoints.student.bootstrap.list_student_labs",
                new=AsyncMock(
                    return_value=[
                        {
                            "id": str(uuid4()),
                            "number": 1,
                            "title": "ЛР 1",
                            "subject_id": str(subject_id),
                            "max_grade": 5,
                            "is_available": True,
                        }
                    ]
                ),
            ),
            patch(
                "app.api.v1.endpoints.student.bootstrap.list_student_attendance_records",
                new=AsyncMock(return_value=[MagicMock(), MagicMock()]),
            ),
            patch(
                "app.api.v1.endpoints.student.bootstrap.build_attendance_stats",
                return_value=attendance_stats_payload(),
            ),
            patch(
                "app.api.v1.endpoints.student.bootstrap.resolve_preferred_attestation_type",
                return_value="first",
            ),
            patch(
                "app.api.v1.endpoints.student.bootstrap.calculate_student_attestation_response",
                new=AsyncMock(
                    return_value={
                        "attestation_type": "first",
                        "subject_id": str(subject_id),
                        "total_score": 32.5,
                        "grade": "5",
                        "is_passing": True,
                    }
                ),
            ) as calculate_mock,
        ):
            async with router_client(
                (router, "/student"),
                dependency_overrides=override_dependencies(mock_user, mock_db),
            ) as client:
                response = await client.get("/student/dashboard/bootstrap")

        assert response.status_code == 200, response.json()
        payload = response.json()
        assert payload["profile"]["full_name"] == "Иванов Иван Иванович"
        assert payload["overview"]["attendance_stats"]["attendance_rate"] == 90.0
        assert payload["overview"]["attestation_type"] == "first"
        assert payload["overview"]["current_attestation"]["total_score"] == 32.5
        calculate_mock.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_multiple_subjects_should_return_subject_selection_error(self):
        mock_user = make_user(group_id=uuid4())
        mock_db = AsyncMock()

        with (
            patch("app.api.v1.endpoints.student.bootstrap.build_student_profile", new=AsyncMock(return_value=profile_payload())),
            patch(
                "app.api.v1.endpoints.student.bootstrap.load_public_semester_info",
                new=AsyncMock(return_value=semester_payload()),
            ),
            patch("app.api.v1.endpoints.student.bootstrap.list_student_announcements", new=AsyncMock(return_value=[])),
            patch(
                "app.api.v1.endpoints.student.bootstrap.list_student_labs",
                new=AsyncMock(
                    return_value=[
                        {"id": str(uuid4()), "number": 1, "title": "ЛР 1", "subject_id": str(uuid4()), "max_grade": 5},
                        {"id": str(uuid4()), "number": 2, "title": "ЛР 2", "subject_id": str(uuid4()), "max_grade": 5},
                    ]
                ),
            ),
            patch("app.api.v1.endpoints.student.bootstrap.list_student_attendance_records", new=AsyncMock(return_value=[])),
            patch("app.api.v1.endpoints.student.bootstrap.build_attendance_stats", return_value=attendance_stats_payload()),
            patch("app.api.v1.endpoints.student.bootstrap.resolve_preferred_attestation_type", return_value="second"),
            patch(
                "app.api.v1.endpoints.student.bootstrap.list_student_attestation_subjects",
                new=AsyncMock(
                    return_value=[
                        AttestationSubjectOption(id=uuid4(), name="Матан"),
                        AttestationSubjectOption(id=uuid4(), name="Физика"),
                    ]
                ),
            ),
            patch(
                "app.api.v1.endpoints.student.bootstrap.calculate_student_attestation_response",
                new=AsyncMock(),
            ) as calculate_mock,
        ):
            async with router_client(
                (router, "/student"),
                dependency_overrides=override_dependencies(mock_user, mock_db),
            ) as client:
                response = await client.get("/student/dashboard/bootstrap")

        assert response.status_code == 200, response.json()
        payload = response.json()
        assert payload["overview"]["attestation_type"] == "second"
        assert payload["overview"]["current_attestation"]["error"] == "Для расчёта аттестации нужно выбрать предмет"
        assert payload["overview"]["current_attestation"]["subject_id"] is None
        calculate_mock.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_business_error_should_fall_back_to_alternate_attestation(self):
        mock_user = make_user(group_id=uuid4())
        mock_db = AsyncMock()
        subject_id = uuid4()

        with (
            patch("app.api.v1.endpoints.student.bootstrap.build_student_profile", new=AsyncMock(return_value=profile_payload())),
            patch(
                "app.api.v1.endpoints.student.bootstrap.load_public_semester_info",
                new=AsyncMock(return_value=semester_payload()),
            ),
            patch("app.api.v1.endpoints.student.bootstrap.list_student_announcements", new=AsyncMock(return_value=[])),
            patch(
                "app.api.v1.endpoints.student.bootstrap.list_student_labs",
                new=AsyncMock(
                    return_value=[
                        {
                            "id": str(uuid4()),
                            "number": 1,
                            "title": "ЛР 1",
                            "subject_id": str(subject_id),
                            "max_grade": 5,
                        }
                    ]
                ),
            ),
            patch("app.api.v1.endpoints.student.bootstrap.list_student_attendance_records", new=AsyncMock(return_value=[])),
            patch("app.api.v1.endpoints.student.bootstrap.build_attendance_stats", return_value=attendance_stats_payload()),
            patch("app.api.v1.endpoints.student.bootstrap.resolve_preferred_attestation_type", return_value="first"),
            patch(
                "app.api.v1.endpoints.student.bootstrap.calculate_student_attestation_response",
                new=AsyncMock(
                    side_effect=[
                        {
                            "attestation_type": "first",
                            "subject_id": str(subject_id),
                            "total_score": 0,
                            "grade": "-",
                            "is_passing": False,
                            "error": "Ошибка расчёта",
                        },
                        {
                            "attestation_type": "second",
                            "subject_id": str(subject_id),
                            "total_score": 28,
                            "grade": "4",
                            "is_passing": True,
                        },
                    ]
                ),
            ) as calculate_mock,
        ):
            async with router_client(
                (router, "/student"),
                dependency_overrides=override_dependencies(mock_user, mock_db),
            ) as client:
                response = await client.get("/student/dashboard/bootstrap")

        assert response.status_code == 200, response.json()
        payload = response.json()
        assert payload["overview"]["current_attestation"]["attestation_type"] == "second"
        assert payload["overview"]["current_attestation"]["total_score"] == 28
        assert [call.args[2] for call in calculate_mock.await_args_list] == ["first", "second"]

    @pytest.mark.asyncio
    async def test_student_without_group_should_return_safe_attestation_error(self):
        mock_user = make_user(group_id=None)
        mock_db = AsyncMock()

        with (
            patch(
                "app.api.v1.endpoints.student.bootstrap.build_student_profile",
                new=AsyncMock(return_value=profile_payload(with_group=False)),
            ),
            patch(
                "app.api.v1.endpoints.student.bootstrap.load_public_semester_info",
                new=AsyncMock(return_value=semester_payload()),
            ),
            patch("app.api.v1.endpoints.student.bootstrap.list_student_announcements", new=AsyncMock(return_value=[])),
            patch("app.api.v1.endpoints.student.bootstrap.list_student_labs", new=AsyncMock(return_value=[])),
            patch("app.api.v1.endpoints.student.bootstrap.list_student_attendance_records", new=AsyncMock(return_value=[])),
            patch(
                "app.api.v1.endpoints.student.bootstrap.build_attendance_stats",
                return_value={
                    "total_classes": 0,
                    "present": 0,
                    "late": 0,
                    "excused": 0,
                    "absent": 0,
                    "attendance_rate": 0.0,
                },
            ),
            patch("app.api.v1.endpoints.student.bootstrap.resolve_preferred_attestation_type", return_value="first"),
        ):
            async with router_client(
                (router, "/student"),
                dependency_overrides=override_dependencies(mock_user, mock_db),
            ) as client:
                response = await client.get("/student/dashboard/bootstrap")

        assert response.status_code == 200, response.json()
        payload = response.json()
        assert payload["profile"]["group"] is None
        assert payload["overview"]["labs"] == []
        assert payload["overview"]["current_attestation"]["error"] == "Студент не привязан к группе"
        assert payload["overview"]["current_attestation"]["is_passing"] is False
