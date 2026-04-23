"""
Калькулятор баллов для аттестации (фасад).
Автобалансировка: веса + количество работ → автоматический расчёт баллов.
"""

from app.models.attendance import Attendance
from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.lesson_grade import LessonGrade

from .attendance_calculator import AttendanceScoreCalculator, AttendanceScoreResult
from .lab_calculator import LabScoreCalculator, LabScoreResult


class AttestationCalculator:
    """
    Калькулятор баллов для аттестации.
    Делегирует расчёты специализированным калькуляторам.
    """

    def __init__(self):
        self._lab_calc = LabScoreCalculator()
        self._attendance_calc = AttendanceScoreCalculator()

    def calculate_labs(
        self,
        lesson_grades: list[LessonGrade],
        settings: AttestationSettings,
        transfer_grades: list[dict] | None = None,
        submission_grades: list[dict] | None = None,
        labs_required_override: int | None = None,
    ) -> LabScoreResult:
        """Расчёт баллов за лабораторные (с учётом снапшотов переводов)"""
        return self._lab_calc.calculate(
            lesson_grades,
            settings,
            transfer_grades,
            submission_grades,
            labs_required_override,
        )

    def calculate_attendance(
        self,
        attendance_records: list[Attendance],
        settings: AttestationSettings,
        expected_lessons: int,
        transfer_attendance: dict[str, int] | None = None,
    ) -> AttendanceScoreResult:
        """Расчёт баллов за посещаемость (фиксированные баллы за занятие)"""
        return self._attendance_calc.calculate(attendance_records, settings, expected_lessons, transfer_attendance)

    def calculate_activity(
        self, activity_points: float, current_score: float, settings: AttestationSettings
    ) -> tuple[float, bool]:
        """
        Расчёт баллов за активность с учётом лимита.

        Логика:
        - Бонусный лимит = attestation_max * (activity_reserve / 100)
        - Если current_score >= max → бонусы заблокированы
        - Штрафы без ограничений

        Returns:
            (activity_score, bonus_blocked)
        """
        if not settings.activity_enabled:
            return 0.0, False

        max_points = settings.attestation_type.max_points
        reserve = settings.get_max_component_points(settings.activity_reserve)

        # Разделяем бонусы и штрафы
        bonus = max(0, activity_points)
        penalty = min(0, activity_points)

        # Проверяем лимит
        remaining = max_points - current_score
        bonus_blocked = remaining <= 0

        if bonus_blocked:
            # Бонусы заблокированы, только штрафы
            return penalty, True

        # Ограничиваем бонусы лимитом активности и оставшимся местом
        max_bonus = min(reserve, remaining)
        capped_bonus = min(bonus, max_bonus)

        return capped_bonus + penalty, False

    def calculate_total(
        self,
        lab_result: LabScoreResult,
        attendance_result: AttendanceScoreResult,
        activity_score: float,
        settings: AttestationSettings,
    ) -> tuple[float, str, bool]:
        """
        Расчёт итогового балла и оценки.

        Returns:
            (total_score, grade, is_passing)
        """
        total = lab_result.score + attendance_result.score + activity_score

        max_points = settings.attestation_type.max_points
        total = max(0, min(total, max_points))

        grade = self._convert_to_grade(total, settings.attestation_type)
        min_passing = AttestationSettings.get_min_passing_points(settings.attestation_type)
        is_passing = total >= min_passing

        return round(total, 2), grade, is_passing

    def _convert_to_grade(self, score: float, attestation_type: AttestationType) -> str:
        """Перевод балла в оценку по шкале университета.
        Логика: [lower, upper) для всех кроме последнего, последний [lower, upper].
        """
        grade_scale = AttestationSettings.get_grade_scale(attestation_type)
        sorted_grades = sorted(grade_scale.items(), key=lambda x: x[1][0])

        for i, (grade_name, (min_val, max_val)) in enumerate(sorted_grades):
            is_last = i == len(sorted_grades) - 1
            if is_last:
                if min_val <= score <= max_val:
                    return str(grade_name)
            else:
                if min_val <= score < max_val:
                    return str(grade_name)

        if score > attestation_type.max_points:
            return "отл"

        return "неуд"
