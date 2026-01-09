"""
Калькулятор баллов для аттестации (фасад).
Автобалансировка: веса + количество работ → автоматический расчёт баллов.
"""
from typing import List

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.attendance import Attendance
from app.models.lesson_grade import LessonGrade

from .lab_calculator import LabScoreCalculator, LabScoreResult
from .attendance_calculator import AttendanceScoreCalculator, AttendanceScoreResult


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
        lesson_grades: List[LessonGrade],
        settings: AttestationSettings,
        transfer_grades: List[dict] = None
    ) -> LabScoreResult:
        """Расчёт баллов за лабораторные (с учётом снапшотов переводов)"""
        return self._lab_calc.calculate(lesson_grades, settings, transfer_grades)
    
    def calculate_attendance(
        self,
        attendance_records: List[Attendance],
        settings: AttestationSettings,
        transfer_attendance: dict = None
    ) -> AttendanceScoreResult:
        """Расчёт баллов за посещаемость (с учётом снапшотов переводов)"""
        return self._attendance_calc.calculate(attendance_records, settings, transfer_attendance)
    
    def calculate_activity(
        self,
        activity_points: float,
        current_score: float,
        settings: AttestationSettings
    ) -> tuple[float, bool]:
        """
        Расчёт баллов за активность с учётом лимита.
        
        Логика:
        - Резерв = attestation_max * (activity_reserve / 100)
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
        
        # Ограничиваем бонусы резервом и оставшимся местом
        max_bonus = min(reserve, remaining)
        capped_bonus = min(bonus, max_bonus)
        
        return capped_bonus + penalty, False
    
    def calculate_total(
        self,
        lab_result: LabScoreResult,
        attendance_result: AttendanceScoreResult,
        activity_score: float,
        settings: AttestationSettings
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
        """Перевод балла в оценку по шкале университета"""
        grade_scale = AttestationSettings.get_grade_scale(attestation_type)
        
        for grade_name, (min_val, max_val) in grade_scale.items():
            if min_val <= score <= max_val:
                return grade_name
        
        if score > attestation_type.max_points:
            return "отл"
        
        return "неуд"
