from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.services.attestation.deadline_validator_batch import get_max_allowed_grades_batch
from app.services.attestation.deadline_validator import get_max_allowed_grade_for_lab
from app.services.attestation.deadline_validator import get_max_allowed_grade
from app.services.deadline_inputs import load_excused_origin_numbers
from app.services.attestation.lab_slot_validator import (
    get_unsubmitted_excused_labs_count,
    is_excused_lab,
)


@pytest.mark.asyncio
async def test_deadline_validator_uses_current_group_origin_lesson(monkeypatch):
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: None))
    db.get = AsyncMock(side_effect=AssertionError("global lab.lesson_id must not be used here"))

    subject_id = uuid4()
    current_lesson = Lesson(
        id=uuid4(),
        group_id=uuid4(),
        subject_id=subject_id,
        date=date(2026, 3, 13),
        lesson_number=2,
        lesson_type=LessonType.LAB,
    )
    origin_lesson = Lesson(
        id=uuid4(),
        group_id=current_lesson.group_id,
        subject_id=subject_id,
        date=date(2026, 2, 20),
        lesson_number=1,
        lesson_type=LessonType.LAB,
    )
    lab = Lab(
        id=uuid4(),
        number=4,
        subject_id=subject_id,
        lesson_id=uuid4(),
        deadline_5_lessons=0,
        deadline_4_lessons=2,
    )

    resolve_origin = AsyncMock(return_value=origin_lesson)
    monkeypatch.setattr(
        "app.services.attestation.deadline_validator._get_origin_lesson_for_group",
        resolve_origin,
    )
    monkeypatch.setattr(
        "app.services.attestation.deadline_validator.load_active_extension_bonus",
        AsyncMock(return_value=0),
    )
    monkeypatch.setattr(
        "app.services.attestation.deadline_validator._get_lesson_positions",
        AsyncMock(return_value={origin_lesson.id: 0, current_lesson.id: 2}),
    )

    result = await get_max_allowed_grade_for_lab(db, lab, current_lesson, student_id=uuid4())

    assert result == 4
    resolve_origin.assert_awaited_once_with(db, current_lesson, lab.number)
    db.get.assert_not_called()


@pytest.mark.asyncio
async def test_unsubmitted_excused_labs_count_uses_excused_work_numbers():
    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            MagicMock(fetchall=lambda: [(3,), (4,)]),
            MagicMock(scalar=lambda: 1),
        ]
    )

    result = await get_unsubmitted_excused_labs_count(db, uuid4(), uuid4())

    assert result == 1


@pytest.mark.asyncio
async def test_is_excused_lab_checks_subject_and_work_number_not_global_lesson_id():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: object()))
    lab = Lab(id=uuid4(), number=3, subject_id=uuid4(), lesson_id=uuid4())

    result = await is_excused_lab(db, uuid4(), lab)

    assert result is True
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_deadline_validator_batch_uses_current_group_origin_not_global_lab_lesson_id(monkeypatch):
    db = AsyncMock()

    subject_id = uuid4()
    student_id = uuid4()
    current_lesson = Lesson(
        id=uuid4(),
        group_id=uuid4(),
        subject_id=subject_id,
        date=date(2026, 3, 13),
        lesson_number=2,
        lesson_type=LessonType.LAB,
    )
    origin_lesson = Lesson(
        id=uuid4(),
        group_id=current_lesson.group_id,
        subject_id=subject_id,
        date=date(2026, 2, 20),
        lesson_number=1,
        lesson_type=LessonType.LAB,
        work_number=4,
    )
    lab = Lab(
        id=uuid4(),
        number=4,
        subject_id=subject_id,
        lesson_id=uuid4(),
        deadline_5_lessons=0,
        deadline_4_lessons=2,
    )

    db.execute = AsyncMock(
        side_effect=[
            MagicMock(fetchall=lambda: []),
        ]
    )

    resolve_origins = AsyncMock(return_value={4: origin_lesson})
    monkeypatch.setattr(
        "app.services.attestation.deadline_validator_batch.find_active_labs_by_subject_and_numbers",
        AsyncMock(return_value={4: lab}),
    )
    monkeypatch.setattr(
        "app.services.attestation.deadline_validator_batch._get_origin_lessons_for_group",
        resolve_origins,
    )
    monkeypatch.setattr(
        "app.services.attestation.deadline_validator_batch.load_active_extension_bonus_map",
        AsyncMock(return_value={}),
    )
    monkeypatch.setattr(
        "app.services.attestation.deadline_validator_batch.load_ordered_deadline_lessons",
        AsyncMock(
            return_value=[
                (origin_lesson.id, origin_lesson.work_number, origin_lesson.date, origin_lesson.lesson_number),
                (current_lesson.id, current_lesson.work_number, current_lesson.date, current_lesson.lesson_number),
            ]
        ),
    )

    result = await get_max_allowed_grades_batch(db, current_lesson, [(student_id, 4)])

    assert result[(student_id, 4)] == 4
    resolve_origins.assert_awaited_once_with(db, current_lesson, {4})


@pytest.mark.asyncio
async def test_deadline_validator_batch_applies_group_extension_bonus(monkeypatch):
    db = AsyncMock()

    subject_id = uuid4()
    student_id = uuid4()
    current_lesson = Lesson(
        id=uuid4(),
        group_id=uuid4(),
        subject_id=subject_id,
        date=date(2026, 3, 13),
        lesson_number=2,
        lesson_type=LessonType.LAB,
    )
    origin_lesson = Lesson(
        id=uuid4(),
        group_id=current_lesson.group_id,
        subject_id=subject_id,
        date=date(2026, 3, 6),
        lesson_number=1,
        lesson_type=LessonType.LAB,
        work_number=4,
    )
    lab = Lab(
        id=uuid4(),
        number=4,
        subject_id=subject_id,
        lesson_id=origin_lesson.id,
        deadline_5_lessons=0,
        deadline_4_lessons=1,
    )

    db.execute = AsyncMock(
        side_effect=[
            MagicMock(scalars=lambda: MagicMock(all=lambda: [lab])),
            MagicMock(fetchall=lambda: []),
        ]
    )

    monkeypatch.setattr(
        "app.services.attestation.deadline_validator_batch.load_active_extension_bonus_map",
        AsyncMock(return_value={lab.id: 1}),
    )
    monkeypatch.setattr(
        "app.services.attestation.deadline_validator_batch.find_active_labs_by_subject_and_numbers",
        AsyncMock(return_value={4: lab}),
    )
    monkeypatch.setattr(
        "app.services.attestation.deadline_validator_batch._get_origin_lessons_for_group",
        AsyncMock(return_value={4: origin_lesson}),
    )
    monkeypatch.setattr(
        "app.services.attestation.deadline_validator_batch.load_ordered_deadline_lessons",
        AsyncMock(
            return_value=[
                (origin_lesson.id, origin_lesson.work_number, origin_lesson.date, origin_lesson.lesson_number),
                (current_lesson.id, current_lesson.work_number, current_lesson.date, current_lesson.lesson_number),
            ]
        ),
    )

    result = await get_max_allowed_grades_batch(db, current_lesson, [(student_id, 4)])

    assert result[(student_id, 4)] == 5


@pytest.mark.asyncio
async def test_excused_origin_numbers_use_origin_lesson_ids_not_any_matching_work_number():
    student_id = uuid4()
    origin_lesson = Lesson(id=uuid4(), group_id=uuid4(), subject_id=uuid4(), lesson_type=LessonType.LAB)
    other_lesson_same_work_number = Lesson(
        id=uuid4(),
        group_id=origin_lesson.group_id,
        subject_id=origin_lesson.subject_id,
        lesson_type=LessonType.LAB,
    )
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(all=lambda: [(origin_lesson.id,)]))

    result = await load_excused_origin_numbers(
        db,
        student_id=student_id,
        origin_lessons_by_number={3: origin_lesson, 4: other_lesson_same_work_number},
    )

    assert result == {3}


@pytest.mark.asyncio
async def test_deadline_validator_uses_shared_active_lab_lookup(monkeypatch):
    db = AsyncMock()
    lesson = Lesson(
        id=uuid4(),
        group_id=uuid4(),
        subject_id=uuid4(),
        date=date(2026, 3, 13),
        lesson_number=2,
        lesson_type=LessonType.LAB,
        work_number=4,
    )
    lab = Lab(id=uuid4(), number=4, subject_id=lesson.subject_id, deadline_5_lessons=1, deadline_4_lessons=2)

    lookup_mock = AsyncMock(return_value=lab)
    grade_mock = AsyncMock(return_value=4)
    monkeypatch.setattr("app.services.attestation.deadline_validator.find_active_lab_by_subject_and_number", lookup_mock)
    monkeypatch.setattr("app.services.attestation.deadline_validator.get_max_allowed_grade_for_lab", grade_mock)

    result = await get_max_allowed_grade(db, lesson, student_id=uuid4())

    assert result == 4
    lookup_mock.assert_awaited_once_with(db, lesson.subject_id, 4)
    grade_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_deadline_validator_batch_uses_shared_active_lab_lookup(monkeypatch):
    db = AsyncMock()
    lesson = Lesson(
        id=uuid4(),
        group_id=uuid4(),
        subject_id=uuid4(),
        date=date(2026, 3, 13),
        lesson_number=2,
        lesson_type=LessonType.LAB,
        work_number=4,
    )
    student_id = uuid4()
    lab = Lab(id=uuid4(), number=4, subject_id=lesson.subject_id, deadline_5_lessons=None, deadline_4_lessons=None)

    lookup_mock = AsyncMock(return_value={4: lab})
    monkeypatch.setattr("app.services.attestation.deadline_validator_batch.find_active_labs_by_subject_and_numbers", lookup_mock)
    monkeypatch.setattr(
        "app.services.attestation.deadline_validator_batch.load_active_extension_bonus_map",
        AsyncMock(return_value={}),
    )
    monkeypatch.setattr(
        "app.services.attestation.deadline_validator_batch._get_origin_lessons_for_group",
        AsyncMock(return_value={}),
    )

    result = await get_max_allowed_grades_batch(db, lesson, [(student_id, 4)])

    assert result[(student_id, 4)] == 5
    lookup_mock.assert_awaited_once_with(db, lesson.subject_id, {4})
