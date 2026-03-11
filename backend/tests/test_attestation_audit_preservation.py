"""
Preservation-тесты для аттестации (Задача 2).

КРИТИЧНО: Эти тесты ДОЛЖНЫ ПРОХОДИТЬ на нефиксированном коде.
Они фиксируют baseline поведение для non-buggy inputs.
После фиксов они должны продолжать проходить (нет регрессий).

Validates: Requirements 3.1–3.11
"""
import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.models.attestation_settings import (
    AttestationSettings,
    AttestationType,
    FIRST_ATTESTATION_WEEK,
    SECOND_ATTESTATION_WEEK,
)
from app.models.attendance import Attendance, AttendanceStatus
from app.services.attestation.attendance_calculator import AttendanceScoreCalculator


# ============================================================
# Preservation 1: FIRST период — без изменений (req 3.1, 3.3)
# ============================================================

class TestFirstPeriodPreservation:
    """FIRST аттестация с semester_start_date — период 0-8 недель без изменений."""

    def test_first_period_with_semester_start(self):
        """
        FIRST с semester_start_date → период (start, start + 8 weeks).
        Это поведение НЕ должно меняться после фиксов.
        """
        semester_start = date(2025, 9, 1)
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=semester_start,
        )

        period_start, period_end = settings.get_effective_period()

        assert period_start == semester_start
        assert period_end == semester_start + timedelta(weeks=FIRST_ATTESTATION_WEEK)

    def test_first_period_duration_is_8_weeks(self):
        """Длительность FIRST периода = 8 недель."""
        semester_start = date(2025, 2, 3)
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=semester_start,
        )

        period_start, period_end = settings.get_effective_period()
        duration_weeks = (period_end - period_start).days / 7

        assert duration_weeks == FIRST_ATTESTATION_WEEK


# ============================================================
# Preservation 2: Явные даты — возвращаются без изменений (req 3.1)
# ============================================================

class TestExplicitDatesPreservation:
    """Явно заданные period_start/end возвращаются без изменений."""

    def test_explicit_dates_returned_as_is_first(self):
        """FIRST с явными датами → возвращает их без изменений."""
        start = date(2025, 9, 15)
        end = date(2025, 11, 10)
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            period_start_date=start,
            period_end_date=end,
        )

        period_start, period_end = settings.get_effective_period()

        assert period_start == start
        assert period_end == end

    def test_explicit_dates_returned_as_is_second(self):
        """SECOND с явными датами → возвращает их без изменений."""
        start = date(2025, 10, 27)
        end = date(2025, 12, 22)
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            period_start_date=start,
            period_end_date=end,
        )

        period_start, period_end = settings.get_effective_period()

        assert period_start == start
        assert period_end == end

    def test_explicit_dates_override_semester_start(self):
        """Явные даты имеют приоритет над semester_start_date."""
        start = date(2025, 9, 15)
        end = date(2025, 11, 10)
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=date(2025, 9, 1),
            period_start_date=start,
            period_end_date=end,
        )

        period_start, period_end = settings.get_effective_period()

        assert period_start == start
        assert period_end == end


# ============================================================
# Preservation 3: Студент без переводов — оценки без изменений (req 3.2)
# ============================================================

class TestNoTransferGradesPreservation:
    """Студент без переводов — _get_lesson_grades() возвращает все оценки."""

    @pytest.mark.asyncio
    async def test_lesson_grades_no_transfer_returns_all(self):
        """
        Студент без переводов → все оценки в периоде возвращаются.
        Поведение не должно меняться после добавления group_id фильтра.
        """
        from app.services.attestation.student_score import StudentScoreCalculator
        from app.models.lesson_grade import LessonGrade

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

        # Все оценки должны вернуться
        assert len(grades) == 2


# ============================================================
# Preservation 4: Все PRESENT/ABSENT — формула без изменений (req 3.4, 3.5)
# ============================================================

class TestPresentAbsentFormulaPreservation:
    """Формула посещаемости для PRESENT/ABSENT не меняется."""

    def _make_record(self, status: AttendanceStatus) -> Attendance:
        r = MagicMock(spec=Attendance)
        r.status = status
        return r

    def test_all_present_gives_max_score(self):
        """Все PRESENT → максимальный балл."""
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )

        records = [self._make_record(AttendanceStatus.PRESENT)] * 10
        calculator = AttendanceScoreCalculator()
        result = calculator.calculate(
            attendance_records=records,
            settings=settings,
            expected_lessons=10,
        )

        max_score = settings.get_max_component_points(settings.attendance_weight)
        assert result.score == pytest.approx(max_score, rel=0.01)

    def test_all_absent_gives_zero_score(self):
        """Все ABSENT с absent_coef=0 → нулевой балл."""
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )

        records = [self._make_record(AttendanceStatus.ABSENT)] * 10
        calculator = AttendanceScoreCalculator()
        result = calculator.calculate(
            attendance_records=records,
            settings=settings,
            expected_lessons=10,
        )

        assert result.score == 0.0

    def test_mixed_present_absent_formula(self):
        """
        7 PRESENT + 3 ABSENT, absent_coef=0 → score = 7/10 * max.
        Формула: (present * 1.0 + absent * absent_coef) * points_per_lesson.
        """
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )

        records = (
            [self._make_record(AttendanceStatus.PRESENT)] * 7
            + [self._make_record(AttendanceStatus.ABSENT)] * 3
        )
        calculator = AttendanceScoreCalculator()
        result = calculator.calculate(
            attendance_records=records,
            settings=settings,
            expected_lessons=10,
        )

        max_score = settings.get_max_component_points(settings.attendance_weight)
        expected_score = 7 / 10 * max_score

        assert result.score == pytest.approx(expected_score, rel=0.01)

    def test_late_coef_applied_correctly(self):
        """LATE с late_coef=0.5 → score = (present + late*0.5) / expected * max."""
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )

        records = (
            [self._make_record(AttendanceStatus.PRESENT)] * 6
            + [self._make_record(AttendanceStatus.LATE)] * 4
        )
        calculator = AttendanceScoreCalculator()
        result = calculator.calculate(
            attendance_records=records,
            settings=settings,
            expected_lessons=10,
        )

        max_score = settings.get_max_component_points(settings.attendance_weight)
        # effective = 6 * 1.0 + 4 * 0.5 = 8.0
        expected_score = 8.0 / 10 * max_score

        assert result.score == pytest.approx(expected_score, rel=0.01)


# ============================================================
# Preservation 5: get_labs_count() — FIRST без изменений (req 3.3)
# ============================================================

class TestLabsCountPreservation:
    """get_labs_count() для FIRST возвращает labs_count_first."""

    def test_first_labs_count_unchanged(self):
        """FIRST → labs_count = labs_count_first (не накопительно)."""
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
        """SECOND → labs_count = first + second (накопительно)."""
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            labs_count_first=8,
            labs_count_second=10,
        )

        # Это текущее поведение — накопительно
        assert settings.get_labs_count() == 18


# ============================================================
# Preservation 6: get_max_component_points() — без изменений
# ============================================================

class TestMaxPointsPreservation:
    """Расчёт максимальных баллов компонентов не меняется."""

    def test_first_max_points(self):
        """FIRST: max = 35, labs_weight=70% → labs_max = 24.5."""
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
        """SECOND: max = 70, labs_weight=70% → labs_max = 49."""
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
        )

        assert settings.get_max_component_points(70.0) == pytest.approx(49.0)
        assert settings.get_max_component_points(20.0) == pytest.approx(14.0)


# ============================================================
# Preservation 7: get_min_expected_lessons() — без изменений
# ============================================================

class TestMinExpectedLessonsPreservation:
    """get_min_expected_lessons() возвращает корректные значения."""

    def test_first_min_expected_lessons(self):
        """FIRST: 2 занятия/неделю * 8 недель = 16."""
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            expected_lessons_per_week=2,
        )

        assert settings.get_min_expected_lessons() == 16

    def test_second_min_expected_lessons(self):
        """SECOND: 2 занятия/неделю * 14 недель = 28."""
        settings = AttestationSettings(
            attestation_type=AttestationType.SECOND,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            expected_lessons_per_week=2,
        )

        assert settings.get_min_expected_lessons() == 28


# ============================================================
# Preservation 8: AttendanceScoreResult поля — без изменений
# ============================================================

class TestAttendanceResultFieldsPreservation:
    """Поля AttendanceScoreResult заполняются корректно."""

    def _make_record(self, status: AttendanceStatus) -> Attendance:
        r = MagicMock(spec=Attendance)
        r.status = status
        return r

    def test_result_fields_populated_correctly(self):
        """Все поля результата заполнены корректно."""
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )

        records = (
            [self._make_record(AttendanceStatus.PRESENT)] * 5
            + [self._make_record(AttendanceStatus.LATE)] * 2
            + [self._make_record(AttendanceStatus.ABSENT)] * 3
        )

        calculator = AttendanceScoreCalculator()
        result = calculator.calculate(
            attendance_records=records,
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
        assert result.score >= 0
        assert result.score <= result.max_score

    def test_score_capped_at_max(self):
        """Балл не превышает максимум."""
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            late_coef=0.5,
            absent_coef=0.0,
        )

        # Больше занятий чем expected → балл не должен превысить max
        records = [self._make_record(AttendanceStatus.PRESENT)] * 20
        calculator = AttendanceScoreCalculator()
        result = calculator.calculate(
            attendance_records=records,
            settings=settings,
            expected_lessons=10,
        )

        assert result.score <= result.max_score


# ============================================================
# Preservation 9: calculate_attestation_period() — FIRST без изменений
# ============================================================

class TestCalculateAttestationPeriodPreservation:
    """calculate_attestation_period() для FIRST не меняется."""

    def test_first_attestation_period_static(self):
        """FIRST: (semester_start, semester_start + 8w)."""
        semester_start = date(2025, 9, 1)
        start, end = AttestationSettings.calculate_attestation_period(
            semester_start, AttestationType.FIRST
        )

        assert start == semester_start
        assert end == semester_start + timedelta(weeks=8)

    def test_period_start_before_end(self):
        """Период всегда start < end."""
        for att_type in [AttestationType.FIRST, AttestationType.SECOND]:
            start, end = AttestationSettings.calculate_attestation_period(
                date(2025, 9, 1), att_type
            )
            assert start < end
