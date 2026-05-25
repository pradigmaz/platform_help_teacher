from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.api.deps import get_current_teacher, get_db
from app.api.v1.endpoints.admin_schedule_view import router
from app.models import User, UserRole
from app.schemas.schedule import (
    GroupedLectureAttendanceSummaryResponse,
    LessonAttendanceSummaryResponse,
    ScheduleParseStatusResponse,
)
from app.services.schedule_attendance_summary import (
    GroupedLectureSummaryResult,
    ScheduleAttendanceSummaryResult,
)
from tests.support.http import router_client


def make_teacher() -> User:
    return User(
        id=uuid4(),
        full_name="Teacher",
        username="teacher",
        role=UserRole.TEACHER,
        is_active=True,
        onboarding_completed=True,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_schedule_view_returns_summary_for_lessons_and_grouped_lectures():
    db = AsyncMock()
    teacher = make_teacher()

    group_id = uuid4()
    lesson_id = uuid4()
    grouped_lesson_id = uuid4()
    subject_id = uuid4()
    lesson_row = SimpleNamespace(
        id=lesson_id,
        group_id=group_id,
        schedule_item_id=None,
        date=date(2026, 4, 2),
        lesson_number=2,
        lesson_type="lab",
        topic="Лаба 1",
        work_id=None,
        work_number=1,
        subgroup=1,
        is_cancelled=False,
        cancellation_reason=None,
        ended_early=False,
        room="108Комп/7к",
        subject=SimpleNamespace(name="Физика"),
        group=SimpleNamespace(name="ИТ-11"),
        subject_id=subject_id,
        offering_id=uuid4(),
    )
    grouped_item = {
        "date": "2026-04-02",
        "lesson_number": 3,
        "subject_id": str(subject_id),
        "subject_name": "Матан",
        "topic": "Интегралы",
        "room": "119Л/7к",
        "is_cancelled": False,
        "ended_early": False,
        "groups": [
            {
                "id": str(group_id),
                "name": "ИТ-11",
                "lesson_id": str(grouped_lesson_id),
            }
        ],
    }

    summary_result = ScheduleAttendanceSummaryResult(
        lesson_summaries={
            lesson_id: LessonAttendanceSummaryResponse(
                state="partial",
                marked_count=5,
                expected_count=8,
                is_past=True,
            )
        },
        grouped_lecture_summaries={
            ("2026-04-02", 3, str(subject_id)): GroupedLectureSummaryResult(
                summary=GroupedLectureAttendanceSummaryResponse(
                    state="complete",
                    marked_count=20,
                    expected_count=20,
                    is_past=True,
                ),
                is_cancelled=False,
                ended_early=True,
            )
        },
    )

    async def override_teacher() -> User:
        return teacher

    async def override_db():
        return db

    with (
        patch(
            "app.api.v1.endpoints.admin_schedule_view._get_parse_status",
            new=AsyncMock(return_value=ScheduleParseStatusResponse(is_running=False, last_run=None)),
        ),
        patch(
            "app.api.v1.endpoints.admin_schedule_view.crud_schedule_parser.get_unresolved_conflicts",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.api.v1.endpoints.admin_schedule_view._get_non_lecture_lessons",
            new=AsyncMock(return_value=[lesson_row]),
        ),
        patch(
            "app.api.v1.endpoints.admin_schedule_view.crud_lesson.get_grouped_lectures",
            new=AsyncMock(return_value=[grouped_item]),
        ),
        patch(
            "app.api.v1.endpoints.admin_schedule_view.schedule_attendance_summary_service.build",
            new=AsyncMock(return_value=summary_result),
        ),
    ):
        async with router_client(
            (router, "/admin"),
            dependency_overrides={
                get_current_teacher: override_teacher,
                get_db: override_db,
            },
        ) as client:
            response = await client.get(
                "/admin/schedule/view",
                params={"start_date": "2026-04-01", "end_date": "2026-04-06"},
            )

    assert response.status_code == 200
    payload = response.json()
    assert payload["lessons"][0]["summary"] == {
        "state": "partial",
        "marked_count": 5,
        "expected_count": 8,
        "is_past": True,
    }
    assert payload["lessons"][0]["room"] == "108Комп/7к"
    assert payload["grouped_lectures"][0]["summary"] == {
        "state": "complete",
        "marked_count": 20,
        "expected_count": 20,
        "is_past": True,
    }
    assert payload["grouped_lectures"][0]["room"] == "119Л/7к"
    assert payload["grouped_lectures"][0]["ended_early"] is True
