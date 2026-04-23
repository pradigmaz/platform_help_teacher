from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.schedule import LessonType
from app.services.attestation.subject_scope import build_period_semester_keys
from app.services.lesson_generator import WEEKDAY_MAP, LessonGenerator
from app.services.schedule_offering_resolution import (
    ResolvedOfferingScope,
    resolve_schedule_offering_scope,
    validate_schedule_item_date_range,
)


def test_build_period_semester_keys_includes_every_semester_in_period():
    assert build_period_semester_keys(date(2025, 9, 1), date(2026, 1, 31)) == ("2025-1",)
    assert build_period_semester_keys(date(2026, 1, 20), date(2026, 2, 10)) == ("2025-1", "2026-2")


@pytest.mark.asyncio
async def test_resolve_schedule_offering_scope_rejects_offering_from_other_semester():
    group_id = uuid4()
    subject_id = uuid4()
    offering_id = uuid4()
    db = AsyncMock()
    db.get.return_value = SimpleNamespace(
        id=offering_id,
        group_id=group_id,
        subject_id=subject_id,
        semester="2025-1",
    )

    with pytest.raises(ValueError, match="не соответствует дате занятия"):
        await resolve_schedule_offering_scope(
            db,
            group_id=group_id,
            reference_date=date(2026, 3, 15),
            subject_id=subject_id,
            offering_id=offering_id,
            require_existing=True,
        )


def test_validate_schedule_item_date_range_rejects_cross_semester_subject_scope():
    with pytest.raises(ValueError, match="не может пересекать границу семестра"):
        validate_schedule_item_date_range(
            start_date=date(2026, 1, 20),
            end_date=date(2026, 2, 10),
            subject_id=uuid4(),
            offering_id=None,
        )


def test_validate_schedule_item_date_range_rejects_end_before_start():
    with pytest.raises(ValueError, match="раньше даты начала"):
        validate_schedule_item_date_range(
            start_date=date(2026, 2, 10),
            end_date=date(2026, 2, 9),
            subject_id=None,
            offering_id=None,
        )


@pytest.mark.asyncio
async def test_lesson_generator_re_resolves_stale_schedule_offering(monkeypatch: pytest.MonkeyPatch):
    group_id = uuid4()
    subject_id = uuid4()
    stale_offering_id = uuid4()
    fresh_offering_id = uuid4()
    lesson_date = date(2026, 2, 2)
    created_scopes: list[tuple[object | None, object | None]] = []

    async def fake_get_by_group(*args, **kwargs):
        return [
            SimpleNamespace(
                id=uuid4(),
                day_of_week=WEEKDAY_MAP[lesson_date.weekday()],
                week_parity=None,
                start_date=lesson_date,
                end_date=None,
                lesson_number=1,
                lesson_type=LessonType.LAB,
                subject_id=subject_id,
                offering_id=stale_offering_id,
                subgroup=None,
            )
        ]

    async def fake_resolve_scope(
        db,
        *,
        group_id,
        reference_date,
        subject_id,
        offering_id,
        ensure=False,
        require_existing=False,
    ):
        created_scopes.append((subject_id, offering_id))
        if offering_id is not None:
            raise ValueError("stale offering")
        return ResolvedOfferingScope(subject_id=subject_id, offering_id=fresh_offering_id)

    async def fake_get_or_create(db, **kwargs):
        assert kwargs["subject_id"] == subject_id
        assert kwargs["offering_id"] == fresh_offering_id
        return SimpleNamespace(id=uuid4())

    monkeypatch.setattr("app.services.lesson_generator.schedule_crud.get_by_group", fake_get_by_group)
    monkeypatch.setattr("app.services.lesson_generator.resolve_schedule_offering_scope", fake_resolve_scope)
    monkeypatch.setattr("app.services.lesson_generator.lesson_crud.get_or_create", fake_get_or_create)

    lessons = await LessonGenerator().generate_lessons_for_period(AsyncMock(), group_id, lesson_date, lesson_date)

    assert len(lessons) == 1
    assert created_scopes == [
        (subject_id, stale_offering_id),
        (subject_id, None),
    ]
