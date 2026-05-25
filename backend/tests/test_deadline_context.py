from datetime import date
from uuid import uuid4

from app.services.deadline_context import (
    build_deadline_context_for_current_lesson,
    build_deadline_context_for_visibility,
)
from app.services.deadline_semantics import evaluate_deadline_state
from app.services.deadline_trace import (
    build_deadline_trace_from_state,
    build_deadline_trace_from_visibility_info,
    resolve_effective_deadline_date,
)
from app.services.lab_visibility.models import LabVisibilityInfo


def test_visibility_deadline_context_keeps_traceable_fields():
    lab_id = uuid4()
    uuid_1, uuid_2 = uuid4(), uuid4()

    context = build_deadline_context_for_visibility(
        lab_number=2,
        ordered_lessons=[
            (uuid_1, 2, date(2026, 3, 1), 1),
            (uuid_2, None, date(2026, 3, 8), 1),
        ],
        past_lesson_ids={uuid_1, uuid_2},
        lab_id=lab_id,
        extensions_map={lab_id: 1},
        excused_lab_numbers={2},
    )

    assert context.lab_number == 2
    assert context.lesson_index == 1
    assert context.extension_bonus == 1
    assert context.is_excused_origin is True


def test_current_lesson_deadline_context_computes_index_from_positions():
    origin_lesson_id = uuid4()
    current_lesson_id = uuid4()

    context = build_deadline_context_for_current_lesson(
        lab_number=4,
        origin_lesson_id=origin_lesson_id,
        current_lesson_id=current_lesson_id,
        lesson_positions={origin_lesson_id: 0, current_lesson_id: 3},
        extension_bonus=2,
    )

    assert context.origin_lesson_id == origin_lesson_id
    assert context.lesson_index == 3
    assert context.extension_bonus == 2
    assert context.is_excused_origin is False


def test_deadline_trace_from_state_keeps_effective_deadlines():
    origin_lesson_id = uuid4()
    current_lesson_id = uuid4()
    context = build_deadline_context_for_current_lesson(
        lab_number=4,
        origin_lesson_id=origin_lesson_id,
        current_lesson_id=current_lesson_id,
        lesson_positions={origin_lesson_id: 0, current_lesson_id: 2},
        extension_bonus=1,
    )
    state = evaluate_deadline_state(
        lesson_index=context.lesson_index or 0,
        deadline_5_lessons=1,
        deadline_4_lessons=3,
        extension_bonus=1,
    )

    trace = build_deadline_trace_from_state(
        context=context,
        state=state,
        deadline_5_lessons=1,
        deadline_4_lessons=3,
    )

    assert trace.current_max_grade == 5
    assert trace.effective_deadline_5_lessons == 2
    assert trace.effective_deadline_4_lessons == 4
    assert trace.extension_bonus == 1


def test_resolve_effective_deadline_date_uses_last_pair_where_grade_is_still_allowed():
    deadline_date = resolve_effective_deadline_date(
        ordered_lessons=[
            (2, date(2026, 3, 1)),
            (None, date(2026, 3, 8)),
            (3, date(2026, 3, 15)),
        ],
        lab_number=2,
        effective_deadline_lessons=1,
    )

    assert deadline_date == date(2026, 3, 8)


def test_deadline_trace_from_visibility_info_reuses_student_side_fields():
    trace = build_deadline_trace_from_visibility_info(
        visibility_info=LabVisibilityInfo(
            lab_number=5,
            is_visible=True,
            current_max_grade=3,
            lesson_index=4,
            extension_bonus=2,
            is_excused_origin=False,
            deadline_5_status="expired",
            deadline_4_status="expired",
            effective_deadline_5_date=date(2026, 3, 8),
            effective_deadline_4_date=date(2026, 3, 15),
        ),
        deadline_5_lessons=1,
        deadline_4_lessons=2,
    )

    assert trace.lesson_index == 4
    assert trace.current_max_grade == 3
    assert trace.effective_deadline_5_lessons == 3
    assert trace.effective_deadline_4_lessons == 4
    assert trace.effective_deadline_5_date == date(2026, 3, 8)
    assert trace.effective_deadline_4_date == date(2026, 3, 15)
