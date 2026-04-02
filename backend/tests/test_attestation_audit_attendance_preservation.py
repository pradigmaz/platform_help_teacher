"""Preservation tests for attendance scoring contracts."""

from unittest.mock import MagicMock

import pytest

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.attendance import Attendance, AttendanceStatus
from app.services.attestation.attendance_calculator import AttendanceScoreCalculator


class TestPresentAbsentFormulaPreservation:
    """Attendance score math for PRESENT/ABSENT/LATE should stay stable."""

    def _make_record(self, status: AttendanceStatus) -> Attendance:
        record = MagicMock(spec=Attendance)
        record.status = status
        return record

    def test_all_present_gives_max_score(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )

        result = AttendanceScoreCalculator().calculate(
            attendance_records=[self._make_record(AttendanceStatus.PRESENT)] * 10,
            settings=settings,
            expected_lessons=10,
        )

        assert result.score == pytest.approx(settings.get_max_component_points(settings.attendance_weight), rel=0.01)

    def test_all_absent_gives_zero_score(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )

        result = AttendanceScoreCalculator().calculate(
            attendance_records=[self._make_record(AttendanceStatus.ABSENT)] * 10,
            settings=settings,
            expected_lessons=10,
        )

        assert result.score == 0.0

    def test_mixed_present_absent_formula(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )

        result = AttendanceScoreCalculator().calculate(
            attendance_records=[self._make_record(AttendanceStatus.PRESENT)] * 7
            + [self._make_record(AttendanceStatus.ABSENT)] * 3,
            settings=settings,
            expected_lessons=10,
        )

        expected_score = 7 / 10 * settings.get_max_component_points(settings.attendance_weight)
        assert result.score == pytest.approx(expected_score, rel=0.01)

    def test_late_coef_applied_correctly(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )

        result = AttendanceScoreCalculator().calculate(
            attendance_records=[self._make_record(AttendanceStatus.PRESENT)] * 6
            + [self._make_record(AttendanceStatus.LATE)] * 4,
            settings=settings,
            expected_lessons=10,
        )

        expected_score = 8.0 / 10 * settings.get_max_component_points(settings.attendance_weight)
        assert result.score == pytest.approx(expected_score, rel=0.01)


class TestAttendanceResultFieldsPreservation:
    """Attendance result fields should remain populated consistently."""

    def _make_record(self, status: AttendanceStatus) -> Attendance:
        record = MagicMock(spec=Attendance)
        record.status = status
        return record

    def test_result_fields_populated_correctly(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )

        result = AttendanceScoreCalculator().calculate(
            attendance_records=[self._make_record(AttendanceStatus.PRESENT)] * 5
            + [self._make_record(AttendanceStatus.LATE)] * 2
            + [self._make_record(AttendanceStatus.ABSENT)] * 3,
            settings=settings,
            expected_lessons=10,
        )

        assert result.present_count == 5
        assert result.late_count == 2
        assert result.absent_count == 3
        assert result.excused_count == 0
        assert result.total_classes == 10
        assert result.expected_lessons == 10
        assert result.max_score == pytest.approx(7.0)
        assert 0 <= result.score <= result.max_score

    def test_score_capped_at_max(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )

        result = AttendanceScoreCalculator().calculate(
            attendance_records=[self._make_record(AttendanceStatus.PRESENT)] * 20,
            settings=settings,
            expected_lessons=10,
        )

        assert result.score <= result.max_score
