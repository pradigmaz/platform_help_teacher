from datetime import date
from uuid import uuid4

from app.services.deadline_context import (
    build_deadline_context_for_current_lesson,
    build_deadline_context_for_visibility,
)
from app.services.deadline_engine import evaluate_deadline_context


def test_deadline_engine_builds_traceable_student_evaluation():
    lab_id = uuid4()
    uuid_1, uuid_2, uuid_3 = uuid4(), uuid4(), uuid4()
    context = build_deadline_context_for_visibility(
        lab_number=2,
        ordered_lessons=[
            (uuid_1, 2, date(2026, 3, 1), 1),
            (uuid_2, None, date(2026, 3, 8), 1),
            (uuid_3, 3, date(2026, 3, 15), 1),
        ],
        past_lesson_ids={uuid_1, uuid_2},
        lab_id=lab_id,
        extensions_map={lab_id: 1},
        excused_lab_numbers=set(),
    )

    evaluation = evaluate_deadline_context(
        context=context,
        deadline_5_lessons=1,
        deadline_4_lessons=2,
        visible_from=date(2026, 3, 1),
        today=date(2026, 3, 15),
    )

    assert evaluation.state.current_max_grade == 5
    assert evaluation.state.deadline_5_status == "active"
    assert evaluation.trace.extension_bonus == 1
    assert evaluation.trace.effective_deadline_5_lessons == 2


def test_deadline_engine_builds_teacher_evaluation_from_same_context_model():
    origin_lesson_id = uuid4()
    current_lesson_id = uuid4()
    context = build_deadline_context_for_current_lesson(
        lab_number=4,
        origin_lesson_id=origin_lesson_id,
        current_lesson_id=current_lesson_id,
        lesson_positions={origin_lesson_id: 0, current_lesson_id: 3},
        extension_bonus=1,
    )

    evaluation = evaluate_deadline_context(
        context=context,
        deadline_5_lessons=1,
        deadline_4_lessons=2,
    )

    assert evaluation.state.lesson_index == 3
    assert evaluation.state.current_max_grade == 4
    assert evaluation.trace.lesson_index == 3
    assert evaluation.trace.effective_deadline_4_lessons == 3
