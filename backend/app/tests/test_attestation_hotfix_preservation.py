"""
Preservation tests for attestation hotfix.
CRITICAL: These tests MUST PASS on BOTH unfixed and fixed code.
They verify that existing correct behavior is not broken by the fix.
"""

from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import settings as hyp_settings
from hypothesis import strategies as st

from app.models.attestation_settings import (
    FIRST_ATTESTATION_WEEK,
    SECOND_ATTESTATION_WEEK,
    AttestationSettings,
    AttestationType,
)
from app.services.attestation.calculator import AttestationCalculator


def make_settings(
    att_type: AttestationType,
    period_start=None,
    period_end=None,
    semester_start=None,
    expected_per_week: int = 2,
) -> SimpleNamespace:
    import types

    s = SimpleNamespace(
        id=uuid4(),
        attestation_type=att_type,
        labs_weight=60.0,
        attendance_weight=37.0,
        activity_reserve=3.0,
        labs_count_first=4,
        labs_count_second=6,
        grade_4_coef=0.68,
        grade_3_coef=0.4,
        late_coef=0.3,
        absent_coef=-0.35,
        self_works_enabled=False,
        self_works_weight=0.0,
        self_works_count=2,
        colloquium_enabled=False,
        colloquium_weight=0.0,
        colloquium_count=1,
        activity_enabled=True,
        expected_lessons_per_week=expected_per_week,
        period_start_date=period_start,
        period_end_date=period_end,
        semester_start_date=semester_start,
    )
    for method_name in (
        "get_min_expected_lessons",
        "get_effective_period",
        "get_max_component_points",
        "get_labs_count",
    ):
        method = getattr(AttestationSettings, method_name, None)
        if method is not None:
            setattr(s, method_name, types.MethodType(method, s))
    return s


# ============================================================
# Preservation A — Explicit periods returned unchanged
# ============================================================


class TestPreservationA_ExplicitPeriods:
    """Explicit period_start/end must be returned as-is after fix."""

    def test_explicit_period_first(self):
        explicit_start = date(2026, 1, 12)
        explicit_end = date(2026, 3, 9)
        s = make_settings(AttestationType.FIRST, period_start=explicit_start, period_end=explicit_end)
        start, end = s.get_effective_period()
        assert start == explicit_start
        assert end == explicit_end

    def test_explicit_period_second(self):
        explicit_start = date(2026, 3, 9)
        explicit_end = date(2026, 4, 20)
        s = make_settings(AttestationType.SECOND, period_start=explicit_start, period_end=explicit_end)
        start, end = s.get_effective_period()
        assert start == explicit_start
        assert end == explicit_end

    @given(
        start_offset=st.integers(min_value=0, max_value=100),
        duration=st.integers(min_value=1, max_value=90),
        att_type=st.sampled_from([AttestationType.FIRST, AttestationType.SECOND]),
    )
    @hyp_settings(max_examples=50)
    def test_explicit_periods_always_returned_unchanged(self, start_offset, duration, att_type):
        base = date(2026, 1, 1)
        explicit_start = base + timedelta(days=start_offset)
        explicit_end = explicit_start + timedelta(days=duration)
        s = make_settings(att_type, period_start=explicit_start, period_end=explicit_end)
        start, end = s.get_effective_period()
        assert start == explicit_start, f"Expected {explicit_start}, got {start}"
        assert end == explicit_end, f"Expected {explicit_end}, got {end}"


# ============================================================
# Preservation B — Successful calculation: is_passing from result
# ============================================================


class TestPreservationB_SuccessfulCalculation:
    """When result is not None, is_passing must come from result, not be overridden."""

    def test_student_builder_valid_result_preserves_is_passing_true(self):
        from app.services.reports.student_builder import build_student_data

        student = MagicMock()
        student.id = uuid4()
        student.full_name = "Test Student"
        student.subgroup = None

        report = MagicMock()
        report.show_names = True
        report.show_grades = True
        report.show_attendance = True
        report.show_notes = False

        result = MagicMock()
        result.is_passing = True
        result.total_score = 25.0
        result.grade = "уд"
        result.breakdown.labs_score = 15.0
        result.breakdown.attendance_score = 8.0
        result.breakdown.activity_score = 2.0

        data = build_student_data(
            student=student,
            result=result,
            att_stats={"rate": 0.9, "present": 12, "absent": 1, "late": 0, "excused": 0},
            lab_stats={"completed": 4, "total": 4},
            notes=[],
            report=report,
        )

        assert data.is_passing is True, f"Expected True, got {data.is_passing}"
        assert data.calculation_error is False, "calculation_error must be False for valid result"

    def test_student_builder_valid_result_preserves_is_passing_false(self):
        from app.services.reports.student_builder import build_student_data

        student = MagicMock()
        student.id = uuid4()
        student.full_name = "Test Student"
        student.subgroup = None

        report = MagicMock()
        report.show_names = True
        report.show_grades = True
        report.show_attendance = True
        report.show_notes = False

        result = MagicMock()
        result.is_passing = False
        result.total_score = 10.0
        result.grade = "неуд"
        result.breakdown.labs_score = 5.0
        result.breakdown.attendance_score = 5.0
        result.breakdown.activity_score = 0.0

        data = build_student_data(
            student=student,
            result=result,
            att_stats={},
            lab_stats={},
            notes=[],
            report=report,
        )

        assert data.is_passing is False
        assert data.calculation_error is False


# ============================================================
# Preservation C — Integer boundary grades unchanged
# ============================================================


class TestPreservationC_IntegerBoundaries:
    """Integer boundary scores must produce same grades after fix."""

    def test_first_attestation_boundaries(self):
        calc = AttestationCalculator()
        cases = [
            (0, "неуд"),
            (10, "неуд"),
            (19, "неуд"),
            (19.99, "неуд"),
            (20, "уд"),
            (25, "уд"),
            (26, "хор"),
            (30, "хор"),
            (31, "отл"),
            (35, "отл"),
        ]
        for score, expected in cases:
            grade = calc._convert_to_grade(score, AttestationType.FIRST)
            assert grade == expected, (
                f"REGRESSION: _convert_to_grade({score}, FIRST) = '{grade}', expected '{expected}'"
            )

    def test_second_attestation_boundaries(self):
        calc = AttestationCalculator()
        cases = [
            (0, "неуд"),
            (39, "неуд"),
            (40, "уд"),
            (50, "уд"),
            (51, "хор"),
            (60, "хор"),
            (61, "отл"),
            (70, "отл"),
        ]
        for score, expected in cases:
            grade = calc._convert_to_grade(score, AttestationType.SECOND)
            assert grade == expected, (
                f"REGRESSION: _convert_to_grade({score}, SECOND) = '{grade}', expected '{expected}'"
            )

    @given(score=st.integers(min_value=0, max_value=35))
    @hyp_settings(max_examples=36)
    def test_all_integer_scores_first_have_valid_grade(self, score):
        calc = AttestationCalculator()
        valid = {"неуд", "уд", "хор", "отл"}
        grade = calc._convert_to_grade(float(score), AttestationType.FIRST)
        assert grade in valid, f"Invalid grade '{grade}' for integer score {score}"


# ============================================================
# Preservation D — Formula invariance
# ============================================================


class TestPreservationD_FormulaInvariance:
    """Total score formula must be unchanged."""

    def test_total_score_formula(self):
        """labs*w1 + attendance*w2 + activity*w3 = total (capped at max)."""
        from app.services.attestation.attendance_calculator import AttendanceScoreResult
        from app.services.attestation.lab_calculator import LabScoreResult

        calc = AttestationCalculator()
        settings = make_settings(AttestationType.FIRST)

        lab_result = LabScoreResult(
            score=15.0, labs_count=3, labs_required=4, max_score=21.0, needs_rework=0, details=[]
        )
        att_result = AttendanceScoreResult(
            score=8.0,
            ratio=0.8,
            max_score=12.95,
            total_classes=10,
            expected_lessons=10,
            present_count=8,
            late_count=0,
            excused_count=0,
            absent_count=2,
        )
        activity_score = 1.0

        total, grade, is_passing = calc.calculate_total(lab_result, att_result, activity_score, settings)

        expected = round(15.0 + 8.0 + 1.0, 2)
        assert total == expected, f"Formula broken: expected {expected}, got {total}"

    @given(
        labs=st.floats(min_value=0.0, max_value=21.0, allow_nan=False),
        att=st.floats(min_value=0.0, max_value=12.95, allow_nan=False),
        act=st.floats(min_value=-5.0, max_value=3.0, allow_nan=False),
    )
    @hyp_settings(max_examples=100)
    def test_total_capped_at_max_points(self, labs, att, act):
        from app.services.attestation.attendance_calculator import AttendanceScoreResult
        from app.services.attestation.lab_calculator import LabScoreResult

        calc = AttestationCalculator()
        settings = make_settings(AttestationType.FIRST)

        lab_result = LabScoreResult(
            score=labs, labs_count=3, labs_required=4, max_score=21.0, needs_rework=0, details=[]
        )
        att_result = AttendanceScoreResult(
            score=att,
            ratio=0.8,
            max_score=12.95,
            total_classes=10,
            expected_lessons=10,
            present_count=8,
            late_count=0,
            excused_count=0,
            absent_count=2,
        )

        total, _, _ = calc.calculate_total(lab_result, att_result, act, settings)
        assert 0.0 <= total <= 35.0, f"Total {total} out of [0, 35] range"


# ============================================================
# Preservation E — min_passing_points static values
# ============================================================


class TestPreservationE_MinPassingPoints:
    """Static min_passing_points values must remain 20 (FIRST) and 40 (SECOND)."""

    def test_first_min_passing(self):
        assert AttestationSettings.get_min_passing_points(AttestationType.FIRST) == 20

    def test_second_min_passing(self):
        assert AttestationSettings.get_min_passing_points(AttestationType.SECOND) == 40
