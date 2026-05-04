from datetime import date
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.student.lab_queries import list_student_labs
from app.models.schedule import LessonType
from app.models.user import User
from app.services.acceptance_lesson_resolver import find_latest_lesson_for_student
from app.services.lab_visibility.models import LabVisibilityInfo


@pytest.mark.asyncio
async def test_list_student_labs_keeps_sequential_gate_within_subject(monkeypatch: pytest.MonkeyPatch):
    student_id = uuid4()
    group_id = uuid4()
    subject_a = uuid4()
    subject_b = uuid4()
    current_user = cast(User, SimpleNamespace(id=student_id, group_id=group_id, subgroup=None))

    def _lab(*, number: int, subject_id, sequential: bool = True):
        return SimpleNamespace(
            id=uuid4(),
            number=number,
            title=f"Lab {number}",
            topic=None,
            description=None,
            subject_id=subject_id,
            deadline_5_lessons=1,
            deadline_4_lessons=None,
            max_grade=5,
            is_sequential=sequential,
            variants=[],
        )

    subject_a_lab_1 = _lab(number=1, subject_id=subject_a)
    subject_b_lab_1 = _lab(number=1, subject_id=subject_b)
    subject_a_lab_2 = _lab(number=2, subject_id=subject_a)
    subject_b_lab_2 = _lab(number=2, subject_id=subject_b)
    ordered_labs = [subject_a_lab_1, subject_b_lab_1, subject_a_lab_2, subject_b_lab_2]

    class _VisibilityService:
        def __init__(self, db):
            self.db = db

        async def get_visible_lab_numbers_by_subject(self, *, group_id, subgroup):
            assert group_id == current_user.group_id
            return {subject_a: {1, 2}, subject_b: {1, 2}}

        async def get_batch_visibility_info(
            self,
            *,
            lab_numbers,
            group_id,
            subgroup,
            labs_deadlines,
            labs_subjects,
            labs_ids,
            student_id,
        ):
            assert group_id == current_user.group_id
            assert student_id == current_user.id
            return {
                lab_number: LabVisibilityInfo(
                    lab_number=lab_number,
                    is_visible=True,
                    current_max_grade=5,
                )
                for lab_number in lab_numbers
            }

    monkeypatch.setattr(
        "app.api.v1.endpoints.student.lab_queries.LabVisibilityService",
        _VisibilityService,
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.lab_queries.list_group_subject_ids_for_current_semester",
        AsyncMock(return_value=[subject_a, subject_b]),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.lab_queries.student_lab_service.get_published_labs",
        AsyncMock(return_value=ordered_labs),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.lab_queries.student_lab_service.get_user_submissions",
        AsyncMock(return_value={}),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.lab_queries.student_lab_service.get_user_journal_grades_by_subject",
        AsyncMock(
            return_value={
                subject_a: {1: SimpleNamespace(grade=5)},
                subject_b: {1: SimpleNamespace(grade=5)},
            }
        ),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.lab_queries.student_lab_service.get_student_position",
        AsyncMock(return_value=None),
    )

    result = await list_student_labs(db=cast(AsyncSession, SimpleNamespace()), current_user=current_user)
    availability = {(item["subject_id"], item["number"]): item["is_available"] for item in result}

    assert availability[(str(subject_b), 1)] is True
    assert availability[(str(subject_a), 2)] is True
    assert availability[(str(subject_b), 2)] is True


@pytest.mark.asyncio
async def test_list_student_labs_rejects_subject_outside_current_offerings(monkeypatch: pytest.MonkeyPatch):
    current_user = cast(User, SimpleNamespace(id=uuid4(), group_id=uuid4(), subgroup=None))
    known_subject = uuid4()
    requested_subject = uuid4()
    get_published_labs = AsyncMock()

    class _VisibilityService:
        def __init__(self, db):
            self.db = db

        async def get_visible_lab_numbers_by_subject(self, *, group_id, subgroup):
            return {known_subject: {1, 2}}

    monkeypatch.setattr("app.api.v1.endpoints.student.lab_queries.LabVisibilityService", _VisibilityService)
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.lab_queries.list_group_subject_ids_for_current_semester",
        AsyncMock(return_value=[known_subject]),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.lab_queries.student_lab_service.get_published_labs",
        get_published_labs,
    )

    result = await list_student_labs(
        db=cast(AsyncSession, SimpleNamespace()),
        current_user=current_user,
        subject_id=requested_subject,
    )

    assert result == []
    get_published_labs.assert_not_awaited()


def _lesson(*, lesson_date: date, lesson_number: int, student, subject_id):
    return SimpleNamespace(
        id=uuid4(),
        date=lesson_date,
        lesson_number=lesson_number,
        lesson_type=LessonType.LAB,
        subject_id=subject_id,
        group_id=student.group_id,
        subgroup=student.subgroup,
        is_cancelled=False,
    )


class _ScalarResult:
    def __init__(self, lessons):
        self._lessons = lessons

    def scalars(self):
        return self

    def all(self):
        return self._lessons


@pytest.mark.asyncio
async def test_find_latest_lesson_for_student_skips_future_same_day_slot(monkeypatch: pytest.MonkeyPatch):
    student = cast(User, SimpleNamespace(group_id=uuid4(), subgroup=1))
    subject_id = uuid4()
    today = date(2026, 4, 22)
    future_slot = _lesson(lesson_date=today, lesson_number=3, student=student, subject_id=subject_id)
    past_slot = _lesson(lesson_date=today, lesson_number=2, student=student, subject_id=subject_id)
    previous_day_slot = _lesson(lesson_date=date(2026, 4, 21), lesson_number=4, student=student, subject_id=subject_id)

    async def fake_execute(_query):
        return _ScalarResult([future_slot, past_slot, previous_day_slot])

    monkeypatch.setattr("app.services.acceptance_lesson_resolver.today_msk", lambda: today)
    monkeypatch.setattr(
        "app.services.acceptance_lesson_resolver.is_schedule_slot_past",
        lambda slot_date, lesson_number: slot_date < today or lesson_number <= 2,
    )

    lesson = await find_latest_lesson_for_student(
        db=cast(AsyncSession, SimpleNamespace(execute=fake_execute)),
        student=student,
        subject_id=subject_id,
    )

    assert lesson is past_slot


@pytest.mark.asyncio
async def test_find_latest_lesson_for_student_keeps_explicit_on_or_before_semantics(
    monkeypatch: pytest.MonkeyPatch,
):
    student = cast(User, SimpleNamespace(group_id=uuid4(), subgroup=1))
    subject_id = uuid4()
    today = date(2026, 4, 22)
    future_slot = _lesson(lesson_date=today, lesson_number=3, student=student, subject_id=subject_id)
    past_slot = _lesson(lesson_date=today, lesson_number=2, student=student, subject_id=subject_id)

    async def fake_execute(_query):
        return _ScalarResult([future_slot, past_slot])

    monkeypatch.setattr(
        "app.services.acceptance_lesson_resolver.is_schedule_slot_past",
        lambda slot_date, lesson_number: False,
    )

    lesson = await find_latest_lesson_for_student(
        db=cast(AsyncSession, SimpleNamespace(execute=fake_execute)),
        student=student,
        subject_id=subject_id,
        on_or_before=today,
    )

    assert lesson is future_slot
