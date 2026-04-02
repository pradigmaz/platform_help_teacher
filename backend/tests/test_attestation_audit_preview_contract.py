"""Contract checks for attestation attendance preview and EXCUSED semantics."""

from unittest.mock import MagicMock

import pytest

from app.models.attendance import Attendance, AttendanceStatus
from app.models.attestation_settings import AttestationSettings, AttestationType
from app.services.attestation.attendance_calculator import AttendanceScoreCalculator
from app.services.attestation.settings import AttestationSettingsManager


class TestAttendancePreviewContract:
    def test_attendance_preview_label_should_be_points_per_lesson(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            labs_count_first=8,
            labs_count_second=10,
            expected_lessons_per_week=2,
        )

        previews = AttestationSettingsManager.build_score_preview(settings)
        attendance_preview = next((preview for preview in previews if "Посещаемость" in preview.component), None)

        assert attendance_preview is not None
        assert attendance_preview.unit_label == "баллов за занятие", (
            f"Counterexample: unit_label='{attendance_preview.unit_label}'"
        )

    def test_attendance_preview_points_per_unit_should_not_be_100(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            labs_count_first=8,
            labs_count_second=10,
            expected_lessons_per_week=2,
        )

        previews = AttestationSettingsManager.build_score_preview(settings)
        attendance_preview = next((preview for preview in previews if "Посещаемость" in preview.component), None)
        assert attendance_preview is not None

        att_max = settings.get_max_component_points(settings.attendance_weight)
        expected_lessons = settings.get_min_expected_lessons()
        expected_ppu = round(att_max / expected_lessons, 2)

        assert attendance_preview.points_per_unit == expected_ppu, (
            f"Counterexample: points_per_unit={attendance_preview.points_per_unit}, expected={expected_ppu}"
        )


class TestExcusedAttendanceContract:
    @staticmethod
    def _make_attendance(status: AttendanceStatus) -> Attendance:
        record = MagicMock(spec=Attendance)
        record.status = status
        return record

    def test_excused_should_reduce_expected_lessons(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )
        records = [self._make_attendance(AttendanceStatus.PRESENT)] * 7 + [
            self._make_attendance(AttendanceStatus.EXCUSED)
        ] * 3

        calculator = AttendanceScoreCalculator()
        result = calculator.calculate(attendance_records=records, settings=settings, expected_lessons=10)
        max_score = settings.get_max_component_points(settings.attendance_weight)

        assert result.score == pytest.approx(max_score, rel=0.01), (
            f"Counterexample: score={result.score}, max={max_score}"
        )

    def test_excused_only_should_give_max_score(self):
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )
        records = [self._make_attendance(AttendanceStatus.EXCUSED)] * 5

        calculator = AttendanceScoreCalculator()
        result = calculator.calculate(attendance_records=records, settings=settings, expected_lessons=5)
        max_score = settings.get_max_component_points(settings.attendance_weight)

        assert result.score == pytest.approx(max_score, rel=0.01), (
            f"Counterexample: score={result.score}, max={max_score}"
        )
