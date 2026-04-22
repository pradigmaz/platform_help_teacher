from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.schedule import LessonType
from app.services.attestation import deadline_validator, deadline_validator_batch
from app.services.deadline_context import build_deadline_context_for_visibility
from app.services.deadline_engine import evaluate_deadline_context
from app.services.deadline_trace import resolve_effective_deadline_date


def _lesson(*, lesson_id, work_number, lesson_date, lesson_number):
    return (lesson_id, work_number, lesson_date, lesson_number)


@pytest.mark.asyncio
async def test_single_validator_uses_current_lesson_subgroup(monkeypatch: pytest.MonkeyPatch):
    group_id = uuid4()
    subject_id = uuid4()
    origin_id = uuid4()
    current_id = uuid4()
    current_lesson = SimpleNamespace(
        id=current_id,
        group_id=group_id,
        subject_id=subject_id,
        subgroup=1,
        lesson_type=LessonType.LAB,
        work_number=None,
    )
    origin_lesson = SimpleNamespace(id=origin_id, group_id=group_id, subject_id=subject_id, date=date(2026, 3, 1))
    lab = SimpleNamespace(id=uuid4(), number=1, deadline_5_lessons=1, deadline_4_lessons=None)
    ordered_lessons = [
        _lesson(lesson_id=origin_id, work_number=1, lesson_date=date(2026, 3, 1), lesson_number=1),
        _lesson(lesson_id=current_id, work_number=None, lesson_date=date(2026, 3, 15), lesson_number=1),
    ]

    async def fake_load_origin_lessons(db, *, group_id, subject_id, work_numbers, subgroup):
        assert subgroup == 1
        return {1: origin_lesson}

    async def fake_load_ordered_deadline_lessons(db, *, group_id, subject_id, subgroup, since_date):
        assert subgroup == 1
        assert since_date == date(2026, 3, 1)
        return ordered_lessons

    async def fake_load_active_extension_bonus(db, *, lab_id, group_id, now):
        return 0

    monkeypatch.setattr(deadline_validator, "load_origin_lessons", fake_load_origin_lessons)
    monkeypatch.setattr(deadline_validator, "load_ordered_deadline_lessons", fake_load_ordered_deadline_lessons)
    monkeypatch.setattr(deadline_validator, "load_active_extension_bonus", fake_load_active_extension_bonus)

    trace = await deadline_validator.get_deadline_trace_for_lab(SimpleNamespace(), lab, current_lesson)

    assert trace is not None
    assert trace.lesson_index == 1
    assert trace.current_max_grade == 5


@pytest.mark.asyncio
async def test_batch_validator_uses_current_lesson_subgroup(monkeypatch: pytest.MonkeyPatch):
    group_id = uuid4()
    subject_id = uuid4()
    student_id = uuid4()
    origin_id = uuid4()
    current_id = uuid4()
    lesson = SimpleNamespace(
        id=current_id,
        group_id=group_id,
        subject_id=subject_id,
        subgroup=1,
        lesson_type=LessonType.LAB,
        work_number=None,
    )
    origin_lesson = SimpleNamespace(id=origin_id, group_id=group_id, subject_id=subject_id, date=date(2026, 3, 1))
    lab = SimpleNamespace(id=uuid4(), number=1, deadline_5_lessons=1, deadline_4_lessons=None)
    ordered_lessons = [
        _lesson(lesson_id=origin_id, work_number=1, lesson_date=date(2026, 3, 1), lesson_number=1),
        _lesson(lesson_id=current_id, work_number=None, lesson_date=date(2026, 3, 15), lesson_number=1),
    ]

    class _Result:
        def fetchall(self):
            return []

    async def fake_execute(query):
        return _Result()

    async def fake_load_origin_lessons(db, *, group_id, subject_id, work_numbers, subgroup):
        assert subgroup == 1
        return {1: origin_lesson}

    async def fake_load_ordered_deadline_lessons(db, *, group_id, subject_id, subgroup, since_date):
        assert subgroup == 1
        return ordered_lessons

    async def fake_find_active_labs(db, subject_id, work_numbers):
        return {1: lab}

    async def fake_load_active_extension_bonus_map(db, *, lab_ids, group_id, now):
        return {}

    db = SimpleNamespace(execute=fake_execute)
    monkeypatch.setattr(deadline_validator_batch, "load_origin_lessons", fake_load_origin_lessons)
    monkeypatch.setattr(deadline_validator_batch, "load_ordered_deadline_lessons", fake_load_ordered_deadline_lessons)
    monkeypatch.setattr(deadline_validator_batch, "find_active_labs_by_subject_and_numbers", fake_find_active_labs)
    monkeypatch.setattr(
        deadline_validator_batch, "load_active_extension_bonus_map", fake_load_active_extension_bonus_map
    )

    result = await deadline_validator_batch.get_max_allowed_grades_batch(db, lesson, [(student_id, 1)])

    assert result[(student_id, 1)] == 5


def test_visibility_waits_for_last_origin_slot_before_starting_deadline():
    first_origin_id = uuid4()
    last_origin_id = uuid4()
    followup_id = uuid4()
    ordered_lessons = [
        _lesson(lesson_id=first_origin_id, work_number=1, lesson_date=date(2026, 3, 1), lesson_number=1),
        _lesson(lesson_id=last_origin_id, work_number=1, lesson_date=date(2026, 3, 1), lesson_number=2),
        _lesson(lesson_id=followup_id, work_number=None, lesson_date=date(2026, 3, 8), lesson_number=1),
    ]
    context = build_deadline_context_for_visibility(
        lab_number=1,
        ordered_lessons=ordered_lessons,
        past_lesson_ids={first_origin_id},
        lab_id=None,
        extensions_map={},
        excused_lab_numbers=set(),
    )

    evaluation = evaluate_deadline_context(
        context=context,
        deadline_5_lessons=1,
        deadline_4_lessons=None,
        visible_from=date(2026, 3, 1),
        today=date(2026, 3, 1),
    )

    assert context.deadline_active is False
    assert context.lesson_index == 0
    assert evaluation.state.deadline_5_status is None
    assert evaluation.state.current_max_grade == 5


def test_visibility_counts_only_past_slots_after_activation():
    origin_id = uuid4()
    past_today_id = uuid4()
    future_today_id = uuid4()
    ordered_lessons = [
        _lesson(lesson_id=origin_id, work_number=1, lesson_date=date(2026, 3, 1), lesson_number=1),
        _lesson(lesson_id=past_today_id, work_number=None, lesson_date=date(2026, 3, 2), lesson_number=1),
        _lesson(lesson_id=future_today_id, work_number=None, lesson_date=date(2026, 3, 2), lesson_number=3),
    ]
    context = build_deadline_context_for_visibility(
        lab_number=1,
        ordered_lessons=ordered_lessons,
        past_lesson_ids={origin_id, past_today_id},
        lab_id=None,
        extensions_map={},
        excused_lab_numbers=set(),
    )

    evaluation = evaluate_deadline_context(
        context=context,
        deadline_5_lessons=1,
        deadline_4_lessons=None,
        visible_from=date(2026, 3, 1),
        today=date(2026, 3, 2),
    )

    assert context.deadline_active is True
    assert context.lesson_index == 1
    assert evaluation.state.deadline_5_status == "active"
    assert evaluation.state.lessons_until_deadline_5 == 0
    assert evaluation.state.current_max_grade == 5


def test_trace_deadline_date_uses_last_origin_slot():
    deadline_date = resolve_effective_deadline_date(
        ordered_lessons=[
            (1, date(2026, 3, 1)),
            (1, date(2026, 3, 1)),
            (None, date(2026, 3, 8)),
        ],
        lab_number=1,
        effective_deadline_lessons=1,
    )

    assert deadline_date == date(2026, 3, 8)
