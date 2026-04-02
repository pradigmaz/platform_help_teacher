"""Contract checks for attestation period semantics and transfer-safe grade loading."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.attestation_settings import (
    SECOND_ATTESTATION_WEEK,
    AttestationSettings,
    AttestationType,
)


class TestSecondFallbackContract:
    def test_second_no_dates_should_raise_value_error(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=None,
            period_start_date=None,
            period_end_date=None,
        )

        with pytest.raises(ValueError, match="semester_start_date"):
            settings.get_effective_period()

    def test_second_no_dates_current_contract(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=None,
            period_start_date=None,
            period_end_date=None,
        )

        with pytest.raises(ValueError, match="semester_start_date"):
            settings.get_effective_period()


class TestTransferGradeIsolationContract:
    @pytest.mark.asyncio
    async def test_lesson_grades_should_filter_by_group_id(self):
        from app.models.lesson_grade import LessonGrade
        from app.services.attestation.student_score import StudentScoreCalculator

        group_b_id = uuid4()
        student_id = uuid4()

        grade_from_a = MagicMock(spec=LessonGrade)
        grade_from_a.student_id = student_id
        grade_from_a.work_number = 1
        grade_from_a.grade = 4

        grade_from_b = MagicMock(spec=LessonGrade)
        grade_from_b.student_id = student_id
        grade_from_b.work_number = 2
        grade_from_b.grade = 5

        mock_db = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [grade_from_a, grade_from_b]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=date(2025, 9, 1),
        )

        calculator = StudentScoreCalculator(mock_db)
        await calculator._get_lesson_grades(student_id, group_b_id, settings)

        query_str = str(mock_db.execute.call_args[0][0])
        assert "group_id" in query_str.lower(), (
            f"Counterexample: SQL запрос не содержит фильтр по group_id. Запрос: {query_str}."
        )


class TestCumulativeSecondPeriodContract:
    def test_second_period_should_be_cumulative_0_to_14_weeks(self):
        semester_start = date(2025, 9, 1)
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=semester_start,
        )

        period_start, period_end = settings.get_effective_period()

        assert period_start == semester_start, (
            f"Counterexample: period_start={period_start}, ожидался {semester_start}."
        )
        assert period_end == semester_start + timedelta(weeks=SECOND_ATTESTATION_WEEK)

    def test_second_labs_count_vs_period_consistency(self):
        semester_start = date(2025, 9, 1)
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=semester_start,
            labs_count_first=8,
            labs_count_second=10,
        )

        labs_count = settings.get_labs_count()
        period_start, period_end = settings.get_effective_period()
        (period_end - period_start).days / 7

        assert period_start == semester_start, (
            f"Counterexample: labs_count={labs_count}, но period_start={period_start}."
        )
