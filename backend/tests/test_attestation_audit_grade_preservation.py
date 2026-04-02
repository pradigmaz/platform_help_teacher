"""Preservation tests for attestation grade and settings contracts."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.attestation_settings import AttestationSettings, AttestationType


class TestNoTransferGradesPreservation:
    """Students without transfers should keep baseline grade lookup behavior."""

    @pytest.mark.asyncio
    async def test_lesson_grades_no_transfer_returns_all(self):
        from app.models.lesson_grade import LessonGrade
        from app.services.attestation.student_score import StudentScoreCalculator

        student_id = uuid4()
        group_id = uuid4()

        grade1 = MagicMock(spec=LessonGrade)
        grade1.student_id = student_id
        grade1.work_number = 1
        grade1.grade = 5

        grade2 = MagicMock(spec=LessonGrade)
        grade2.student_id = student_id
        grade2.work_number = 2
        grade2.grade = 4

        mock_db = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [grade1, grade2]
        mock_result = MagicMock()
        mock_result.all.return_value = [(grade1, None), (grade2, None)]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=date(2025, 9, 1),
        )

        calculator = StudentScoreCalculator(mock_db)
        grades = await calculator._get_lesson_grades(student_id, group_id, settings)

        assert len(grades) == 2


class TestLabsCountPreservation:
    """Lab count semantics should stay stable for both periods."""

    def test_first_labs_count_unchanged(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            labs_count_first=8,
            labs_count_second=10,
        )

        assert settings.get_labs_count() == 8

    def test_second_labs_count_is_cumulative(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            labs_count_first=8,
            labs_count_second=10,
        )

        assert settings.get_labs_count() == 18


class TestMaxPointsPreservation:
    """Component max-point calculation should remain unchanged."""

    def test_first_max_points(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
        )

        assert settings.get_max_component_points(70.0) == pytest.approx(24.5)
        assert settings.get_max_component_points(20.0) == pytest.approx(7.0)
        assert settings.get_max_component_points(10.0) == pytest.approx(3.5)

    def test_second_max_points(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
        )

        assert settings.get_max_component_points(70.0) == pytest.approx(49.0)
        assert settings.get_max_component_points(20.0) == pytest.approx(14.0)


class TestMinExpectedLessonsPreservation:
    """Minimum expected lessons should remain period-aware."""

    def test_first_min_expected_lessons(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            expected_lessons_per_week=2,
        )

        assert settings.get_min_expected_lessons() == 16

    def test_second_min_expected_lessons(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            expected_lessons_per_week=2,
        )

        assert settings.get_min_expected_lessons() == 28
