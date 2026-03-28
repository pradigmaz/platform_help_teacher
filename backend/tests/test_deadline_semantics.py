from datetime import date

from app.services.deadline_semantics import (
    apply_extension_bonus,
    calculate_visibility_state,
    evaluate_deadline_state,
    max_allowed_grade_for_lesson_index,
)


def test_max_allowed_grade_respects_next_pair_semantics():
    assert max_allowed_grade_for_lesson_index(lesson_index=1, deadline_5_lessons=1, deadline_4_lessons=None) == 5
    assert max_allowed_grade_for_lesson_index(lesson_index=2, deadline_5_lessons=1, deadline_4_lessons=None) == 4


def test_max_allowed_grade_applies_extension_bonus():
    assert (
        max_allowed_grade_for_lesson_index(
            lesson_index=1,
            deadline_5_lessons=0,
            deadline_4_lessons=1,
            extension_bonus=1,
        )
        == 5
    )


def test_visibility_state_matches_teacher_side_thresholds():
    state = calculate_visibility_state(
        lessons_after=2,
        visible_from=date(2026, 3, 1),
        today=date(2026, 3, 15),
        deadline_5_lessons=1,
        deadline_4_lessons=2,
    )

    assert state.deadline_5_status == "expired"
    assert state.deadline_4_status == "active"
    assert state.lessons_until_deadline_4 == 0
    assert state.current_max_grade == 4
    assert state.lesson_index == 2


def test_excused_origin_overrides_deadline_limits():
    state = calculate_visibility_state(
        lessons_after=10,
        visible_from=date(2026, 3, 1),
        today=date(2026, 3, 15),
        deadline_5_lessons=0,
        deadline_4_lessons=1,
        extension_bonus=5,
        is_excused_origin=True,
    )

    assert state.current_max_grade == 5
    assert state.deadline_5_status is None
    assert state.deadline_4_status is None


def test_apply_extension_bonus_keeps_none_deadline():
    assert apply_extension_bonus(None, 3) is None
    assert apply_extension_bonus(2, 3) == 5


def test_evaluate_deadline_state_supports_teacher_and_student_views():
    teacher_state = evaluate_deadline_state(
        lesson_index=3,
        deadline_5_lessons=1,
        deadline_4_lessons=2,
    )
    student_state = evaluate_deadline_state(
        lesson_index=3,
        deadline_5_lessons=1,
        deadline_4_lessons=2,
        visible_from=date(2026, 3, 1),
        today=date(2026, 3, 15),
    )

    assert teacher_state.current_max_grade == 3
    assert teacher_state.deadline_5_status is None
    assert student_state.current_max_grade == teacher_state.current_max_grade
    assert student_state.deadline_5_status == "expired"
