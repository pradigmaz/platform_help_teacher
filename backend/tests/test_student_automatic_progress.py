from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.services.attestation.automatic_queue import build_automatic_queue_entries


def _student(student_id, name: str):
    return SimpleNamespace(id=student_id, full_name=name)


def test_build_automatic_queue_entries_ranks_full_completions_by_earliest_finish():
    student_fast = uuid4()
    student_slow = uuid4()
    completion_map = {
        student_fast: {
            1: datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
            2: datetime(2026, 4, 2, 10, 0, tzinfo=UTC),
            3: datetime(2026, 4, 3, 10, 0, tzinfo=UTC),
        },
        student_slow: {
            1: datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
            2: datetime(2026, 4, 2, 9, 0, tzinfo=UTC),
            3: datetime(2026, 4, 4, 9, 0, tzinfo=UTC),
        },
    }

    entries = build_automatic_queue_entries(
        students=[_student(student_fast, "Быстрый"), _student(student_slow, "Медленный")],
        completion_map=completion_map,
        total_labs=3,
        automatic_places=1,
        declined_by_student_id={},
    )

    assert entries[0].student_id == student_fast
    assert entries[0].completed_count == 3
    assert entries[0].automatic_remaining == 0
    assert entries[0].queue_position == 1
    assert entries[0].is_winner is True
    assert entries[0].completion_at == datetime(2026, 4, 3, 10, 0, tzinfo=UTC)
    assert entries[1].student_id == student_slow
    assert entries[1].queue_position == 2


def test_build_automatic_queue_entries_uses_stable_student_id_tie_break():
    student_a = uuid4()
    student_b = uuid4()
    same_finish = datetime(2026, 4, 3, 10, 0, tzinfo=UTC)
    completion_map = {
        student_a: {1: datetime(2026, 4, 1, 10, 0, tzinfo=UTC), 2: same_finish},
        student_b: {1: datetime(2026, 4, 1, 10, 0, tzinfo=UTC), 2: same_finish},
    }

    entries = build_automatic_queue_entries(
        students=[_student(student_a, "Студент A"), _student(student_b, "Студент B")],
        completion_map=completion_map,
        total_labs=2,
        automatic_places=1,
        declined_by_student_id={},
    )

    if str(student_a) < str(student_b):
        assert entries[0].student_id == student_a
        assert entries[0].queue_position == 1
        assert entries[1].queue_position == 2
    else:
        assert entries[0].student_id == student_b
        assert entries[0].queue_position == 1
        assert entries[1].queue_position == 2


def test_build_automatic_queue_entries_skips_declined_winner_and_promotes_next_student():
    student_first = uuid4()
    student_second = uuid4()
    student_third = uuid4()
    completion_map = {
        student_first: {
            1: datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
            2: datetime(2026, 4, 2, 10, 0, tzinfo=UTC),
        },
        student_second: {
            1: datetime(2026, 4, 1, 11, 0, tzinfo=UTC),
            2: datetime(2026, 4, 2, 11, 0, tzinfo=UTC),
        },
        student_third: {
            1: datetime(2026, 4, 1, 12, 0, tzinfo=UTC),
            2: datetime(2026, 4, 2, 12, 0, tzinfo=UTC),
        },
    }

    entries = build_automatic_queue_entries(
        students=[
            _student(student_first, "Первый"),
            _student(student_second, "Второй"),
            _student(student_third, "Третий"),
        ],
        completion_map=completion_map,
        total_labs=2,
        automatic_places=1,
        declined_by_student_id={student_first: "Пошёл на экзамен"},
    )

    declined_entry = next(entry for entry in entries if entry.student_id == student_first)
    promoted_entry = next(entry for entry in entries if entry.student_id == student_second)
    waiting_entry = next(entry for entry in entries if entry.student_id == student_third)

    assert promoted_entry.queue_position == 1
    assert promoted_entry.is_winner is True
    assert waiting_entry.queue_position == 2
    assert waiting_entry.is_winner is False
    assert declined_entry.queue_position is None
    assert declined_entry.is_winner is False
    assert declined_entry.is_declined is True
    assert declined_entry.declined_reason == "Пошёл на экзамен"
