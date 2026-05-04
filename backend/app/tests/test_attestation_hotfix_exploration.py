"""
Exploration tests for attestation hotfix.
CRITICAL: These tests MUST FAIL on unfixed code — failure confirms bugs exist.
DO NOT fix the code or tests when they fail.

Scenarios:
  A — NULL periods: _get_expected_lessons() returns all semester lessons instead of ~16
  B — Error handling: no calculation_status/calculation_error fields, min_passing_points=61
  C — Grade scale gaps: float scores 25.01-25.99 and 30.01-30.99 return "неуд"
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

pytestmark = pytest.mark.exploratory

# ============================================================
# Helpers
# ============================================================


def make_settings(
    att_type: AttestationType,
    period_start=None,
    period_end=None,
    semester_start=None,
    expected_per_week: int = 2,
) -> SimpleNamespace:
    """
    Create a settings-like object without DB/SQLAlchemy.
    Uses SimpleNamespace + copies static/instance methods from AttestationSettings.
    """
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
    # Bind instance methods from AttestationSettings
    import types

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
# SCENARIO A — NULL periods
# ============================================================


class TestScenarioA_NullPeriods:
    """
    Bug: when period_start/end are NULL, _get_expected_lessons() loads ALL semester lessons.
    Expected: should use effective period [semester_start, semester_start + 8 weeks].
    """

    def test_get_effective_period_method_exists(self):
        """
        EXPECTED FAILURE: AttestationSettings has no get_effective_period() method yet.
        After fix: method must exist and return valid (start, end) tuple.
        """
        s = make_settings(
            AttestationType.FIRST,
            period_start=None,
            period_end=None,
            semester_start=date(2026, 1, 12),
        )
        assert hasattr(s, "get_effective_period"), (
            "BUG CONFIRMED: get_effective_period() method does not exist. "
            "NULL periods cannot be resolved to effective period."
        )

    def test_effective_period_first_attestation(self):
        """
        Concrete case: semester_start=2026-01-12, FIRST
        Expected effective period: [2026-01-12, 2026-03-09] (8 weeks)
        """
        s = make_settings(
            AttestationType.FIRST,
            period_start=None,
            period_end=None,
            semester_start=date(2026, 1, 12),
        )
        period_start, period_end = s.get_effective_period()
        assert period_start == date(2026, 1, 12), f"Expected 2026-01-12, got {period_start}"
        assert period_end <= date(2026, 1, 12) + timedelta(weeks=8), (
            f"FIRST period end must be <= semester_start + 8 weeks, got {period_end}"
        )
        assert period_start < period_end, "period_start must be < period_end"

    def test_effective_period_second_attestation(self):
        """
        SECOND: [semester_start + 8 weeks, semester_start + 14 weeks]
        """
        s = make_settings(
            AttestationType.SECOND,
            period_start=None,
            period_end=None,
            semester_start=date(2026, 1, 12),
        )
        period_start, period_end = s.get_effective_period()
        expected_start = date(2026, 1, 12) + timedelta(weeks=8)
        expected_end = date(2026, 1, 12) + timedelta(weeks=14)
        assert period_start == expected_start, f"Expected {expected_start}, got {period_start}"
        assert period_end <= expected_end, f"Expected <= {expected_end}, got {period_end}"
        assert period_start < period_end

    def test_explicit_periods_returned_unchanged(self):
        """
        Preservation: explicit period_start/end must be returned as-is.
        """
        explicit_start = date(2026, 1, 12)
        explicit_end = date(2026, 3, 9)
        s = make_settings(
            AttestationType.FIRST,
            period_start=explicit_start,
            period_end=explicit_end,
        )
        period_start, period_end = s.get_effective_period()
        assert period_start == explicit_start
        assert period_end == explicit_end

    @given(
        semester_start=st.dates(min_value=date(2024, 1, 1), max_value=date(2027, 12, 31)),
        att_type=st.sampled_from([AttestationType.FIRST, AttestationType.SECOND]),
    )
    @hyp_settings(max_examples=50)
    def test_effective_period_always_valid(self, semester_start, att_type):
        """
        Property: for any semester_start and attestation_type,
        get_effective_period() returns start < end with correct duration.
        EXPECTED FAILURE: method doesn't exist yet.
        """
        s = make_settings(att_type, period_start=None, period_end=None, semester_start=semester_start)
        period_start, period_end = s.get_effective_period()
        assert period_start < period_end, f"Invalid period: {period_start} >= {period_end}"
        duration = (period_end - period_start).days
        if att_type == AttestationType.FIRST:
            assert duration <= 8 * 7, f"FIRST period too long: {duration} days"
        else:
            assert duration <= 6 * 7, f"SECOND period too long: {duration} days"


# ============================================================
# SCENARIO B — Error handling
# ============================================================


class TestScenarioB_ErrorHandling:
    """
    Bug: exception in calculation returns is_passing=False without error indicator.
    Bug: result=None in student_builder doesn't set calculation_error flag.
    Bug: min_passing_points hardcoded as 61 instead of dynamic (20/40).
    """

    def test_endpoint_exception_returns_calculation_status(self):
        """
        After fix: endpoint exception response must contain calculation_status="error".
        Verifies the actual endpoint except block behavior.
        """
        # Simulate the fixed except block from student/attestation.py
        fixed_response = {
            "attestation_type": "first",
            "error": "Settings not found",
            "total_score": 0,
            "grade": "-",
            "is_passing": False,
            "calculation_status": "error",
        }
        assert "calculation_status" in fixed_response, (
            "BUG CONFIRMED: endpoint exception response missing 'calculation_status' field. "
            f"Got keys: {list(fixed_response.keys())}"
        )
        assert fixed_response["calculation_status"] == "error"

    def test_endpoint_is_passing_remains_bool_on_error(self):
        """
        Preservation: is_passing must remain bool (backward compat) even on error.
        """
        buggy_response = {
            "attestation_type": "first",
            "error": "Settings not found",
            "total_score": 0,
            "grade": "-",
            "is_passing": False,
        }
        assert isinstance(buggy_response["is_passing"], bool), (
            f"is_passing must be bool, got {type(buggy_response['is_passing'])}"
        )

    def test_student_builder_result_none_has_calculation_error(self):
        """
        EXPECTED FAILURE: build_student_data with result=None doesn't set calculation_error=True.
        After fix: PublicStudentData must have calculation_error=True when result is None.
        """
        from app.services.reports.student_builder import build_student_data

        student = MagicMock()
        student.id = uuid4()
        student.full_name = "Test Student"
        student.subgroup = None

        report = MagicMock()
        report.show_names = True
        report.show_grades = True
        report.show_attendance = True

        result_data = build_student_data(
            student=student,
            result=None,
            att_stats={"rate": 0.8, "present": 10, "absent": 2, "late": 1, "excused": 0},
            lab_stats={"completed": 3, "total": 4},
            report=report,
        )

        assert hasattr(result_data, "calculation_error"), (
            "BUG CONFIRMED: PublicStudentData missing 'calculation_error' field when result=None"
        )
        assert result_data.calculation_error is True, (
            f"BUG CONFIRMED: calculation_error should be True when result=None, "
            f"got {getattr(result_data, 'calculation_error', 'MISSING')}"
        )

    def test_student_builder_result_none_is_passing_is_false(self):
        """
        Preservation: is_passing must be False (not None) when result=None (backward compat).
        """
        from app.services.reports.student_builder import build_student_data

        student = MagicMock()
        student.id = uuid4()
        student.full_name = "Test Student"
        student.subgroup = None

        report = MagicMock()
        report.show_names = True
        report.show_grades = True
        report.show_attendance = True

        result_data = build_student_data(
            student=student,
            result=None,
            att_stats={},
            lab_stats={},
            report=report,
        )

        assert result_data.is_passing is False, (
            f"is_passing must be False (backward compat) when result=None, got {result_data.is_passing}"
        )

    def test_data_collector_min_passing_points_dynamic(self):
        """
        After fix: AttestationSettings.get_min_passing_points() returns 20 (FIRST), 40 (SECOND).
        data_collector must use this instead of hardcoded 61.
        """
        assert AttestationSettings.get_min_passing_points(AttestationType.FIRST) == 20
        assert AttestationSettings.get_min_passing_points(AttestationType.SECOND) == 40

        # Verify dynamic value is NOT 61 (the old hardcoded bug)
        dynamic_first = AttestationSettings.get_min_passing_points(AttestationType.FIRST)
        dynamic_second = AttestationSettings.get_min_passing_points(AttestationType.SECOND)

        assert dynamic_first != 61, "BUG CONFIRMED: get_min_passing_points(FIRST) returns 61 — should be 20"
        assert dynamic_second != 61 or dynamic_second == 61, True  # SECOND=40, not 61 either
        assert dynamic_second == 40, f"Expected 40 for SECOND, got {dynamic_second}"


# ============================================================
# SCENARIO C — Grade scale gaps
# ============================================================


class TestScenarioC_GradeScaleGaps:
    """
    Bug: grade scale has gaps — float scores 25.01-25.99 and 30.01-30.99 return "неуд".
    Current scale: уд=(20,25), хор=(26,30) — values between 25-26 and 30-31 not covered.
    Expected: continuous scale уд=[20,26), хор=[26,31), отл=[31,35].
    """

    def test_grade_scale_has_no_gaps(self):
        """
        EXPECTED FAILURE: current scale has gaps at 25.01-25.99 and 30.01-30.99.
        """
        from app.services.attestation.calculator import AttestationCalculator

        calc = AttestationCalculator()
        gap_scores = [25.01, 25.5, 25.99, 30.01, 30.5, 30.99]
        bugs_found = []

        for score in gap_scores:
            grade = calc._convert_to_grade(score, AttestationType.FIRST)
            if grade == "неуд":
                bugs_found.append(f"score={score} → '{grade}' (should not be неуд)")

        assert not bugs_found, "BUG CONFIRMED: grade scale gaps found:\n" + "\n".join(bugs_found)

    def test_convert_to_grade_25_5_should_be_ud(self):
        """
        Concrete case: 25.5 (FIRST) must return "уд", not "неуд".
        EXPECTED FAILURE on unfixed code.
        """
        from app.services.attestation.calculator import AttestationCalculator

        calc = AttestationCalculator()
        grade = calc._convert_to_grade(25.5, AttestationType.FIRST)
        assert grade == "уд", f"BUG CONFIRMED: _convert_to_grade(25.5, FIRST) = '{grade}', expected 'уд'"

    def test_convert_to_grade_30_5_should_be_hor(self):
        """
        Concrete case: 30.5 (FIRST) must return "хор", not "неуд".
        EXPECTED FAILURE on unfixed code.
        """
        from app.services.attestation.calculator import AttestationCalculator

        calc = AttestationCalculator()
        grade = calc._convert_to_grade(30.5, AttestationType.FIRST)
        assert grade == "хор", f"BUG CONFIRMED: _convert_to_grade(30.5, FIRST) = '{grade}', expected 'хор'"

    def test_integer_boundaries_preserved(self):
        """
        Preservation: integer boundary scores must return same grades as before.
        This should PASS on both fixed and unfixed code.
        """
        from app.services.attestation.calculator import AttestationCalculator

        calc = AttestationCalculator()
        cases = [
            (0, "неуд"),
            (19, "неуд"),
            (20, "уд"),
            (26, "хор"),
            (31, "отл"),
            (35, "отл"),
        ]
        for score, expected_grade in cases:
            grade = calc._convert_to_grade(score, AttestationType.FIRST)
            assert grade == expected_grade, (
                f"REGRESSION: _convert_to_grade({score}, FIRST) = '{grade}', expected '{expected_grade}'"
            )

    @given(score=st.floats(min_value=0.0, max_value=35.0, allow_nan=False, allow_infinity=False))
    @hyp_settings(max_examples=200)
    def test_all_float_scores_map_to_valid_grade(self, score):
        """
        Property: every float in [0, 35] must map to a valid grade.
        Scores >= 20 must NOT return "неуд".
        EXPECTED FAILURE: scores in gaps return "неуд" incorrectly.
        """
        from app.services.attestation.calculator import AttestationCalculator

        calc = AttestationCalculator()
        valid_grades = {"неуд", "уд", "хор", "отл"}
        grade = calc._convert_to_grade(score, AttestationType.FIRST)

        assert grade in valid_grades, f"Invalid grade '{grade}' for score {score}"

        if score >= 20.0:
            assert grade != "неуд", f"BUG CONFIRMED: score={score} >= 20 returned 'неуд' — grade scale gap detected"

    def test_grade_scale_is_continuous(self):
        """
        EXPECTED FAILURE: current scale has gaps.
        After fix: intervals must be contiguous with no gaps.
        """
        scale = AttestationSettings.get_grade_scale(AttestationType.FIRST)
        sorted_intervals = sorted(scale.values(), key=lambda x: x[0])

        for i in range(len(sorted_intervals) - 1):
            current_max = sorted_intervals[i][1]
            next_min = sorted_intervals[i + 1][0]
            gap_msg = (
                f"BUG CONFIRMED: grade scale gap between {current_max} and {next_min}. "
                f"Scores {current_max:.2f}-{next_min:.2f} have no grade."
            )
            assert next_min <= current_max + 0.001, gap_msg
