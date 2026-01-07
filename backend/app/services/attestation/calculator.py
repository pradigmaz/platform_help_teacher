"""
Калькулятор баллов для аттестации.

Фасад для модулей lab_calculator, attendance_calculator, work_calculator.
Реализует:
- Requirements 2.1-2.7: расчёт баллов за лабораторные с учётом дедлайнов
- Requirements 3.2-3.7: расчёт баллов за посещаемость
- Requirements 4.1-4.4: итоговый расчёт и перевод в оценки
"""
from typing import List

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.attendance import Attendance
from app.models.submission import Submission
from app.models.lab import Lab
from app.models.work import Work
from app.models.work_submission import WorkSubmission
from app.models.lesson_grade import LessonGrade

from .models import LabScoreResult, AttendanceScoreResult, WorkScoreResult
from .lab_calculator import LabScoreCalculator
from .attendance_calculator import AttendanceScoreCalculator
from .work_calculator import WorkScoreCalculator


class AttestationCalculator:
    """
    Калькулятор баллов для аттестации.
    
    Stateless класс с чистыми функциями расчёта.
    Делегирует расчёты специализированным калькуляторам.
    """
    
    def __init__(self):
        self._lab_calc = LabScoreCalculator()
        self._attendance_calc = AttendanceScoreCalculator()
        self._work_calc = WorkScoreCalculator()
    
    def calculate_lab_score(
        self,
        submissions: List[Submission],
        labs: List[Lab],
        settings: AttestationSettings
    ) -> LabScoreResult:
        """Расчёт баллов за лабораторные работы из Submission."""
        return self._lab_calc.calculate_from_submissions(submissions, labs, settings)
    
    def _calculate_deadline_coefficient(
        self,
        submission: Submission,
        lab: Lab,
        settings: AttestationSettings
    ) -> float:
        """Расчёт коэффициента дедлайна для работы."""
        return self._lab_calc._calculate_deadline_coefficient(submission, lab, settings)

    def calculate_lesson_grades_score(
        self,
        lesson_grades: List[LessonGrade],
        settings: AttestationSettings
    ) -> LabScoreResult:
        """Расчёт баллов за лабораторные на основе LessonGrade."""
        return self._lab_calc.calculate_from_lesson_grades(lesson_grades, settings)
    
    def calculate_attendance_score(
        self,
        attendance_records: List[Attendance],
        settings: AttestationSettings
    ) -> AttendanceScoreResult:
        """Расчёт баллов за посещаемость."""
        return self._attendance_calc.calculate(attendance_records, settings)
    
    def calculate_activity_score(
        self,
        activity_points: float,
        settings: AttestationSettings
    ) -> float:
        """Расчёт баллов за активность."""
        if not settings.activity_enabled:
            return 0.0
        return (activity_points * settings.activity_weight / 100)

    def calculate_work_score(
        self,
        submissions: List[WorkSubmission],
        works: List[Work],
        weight: float,
        grading_scale: int = 10
    ) -> WorkScoreResult:
        """Расчёт баллов за работы."""
        return self._work_calc.calculate(submissions, works, weight, grading_scale)
    
    def calculate_total_score(
        self,
        lab_result: LabScoreResult,
        attendance_result: AttendanceScoreResult,
        activity_score: float,
        settings: AttestationSettings
    ) -> tuple[float, str, bool]:
        """
        Расчёт итогового балла и оценки.
        
        Requirements:
        - 4.1: sum weighted components
        - 4.2: cap at max points (35 for first, 70 for second)
        - 4.3, 4.4: convert to grade using fixed university scales
        """
        total = (
            lab_result.weighted_score +
            attendance_result.weighted_score +
            activity_score
        )
        
        max_points = AttestationSettings.get_max_points(settings.attestation_type)
        total = min(total, max_points)
        total = max(0, total)
        
        grade = self._convert_to_grade(total, settings.attestation_type)
        
        min_passing = AttestationSettings.get_min_passing_points(settings.attestation_type)
        is_passing = total >= min_passing
        
        return total, grade, is_passing
    
    def _convert_to_grade(self, score: float, attestation_type: AttestationType) -> str:
        """
        Перевод балла в оценку по фиксированной шкале университета.
        
        Requirements 4.3, 4.4:
        - First attestation: 1-19.99=неуд, 20-25=уд, 26-30=хор, 31-35=отл
        - Second attestation: 1-39.99=неуд, 40-50=уд, 51-60=хор, 61-70=отл
        """
        grade_scale = AttestationSettings.get_grade_scale(attestation_type)
        
        for grade_name, (min_val, max_val) in grade_scale.items():
            if min_val <= score <= max_val:
                return grade_name
        
        if score > AttestationSettings.get_max_points(attestation_type):
            return "отл"
        
        return "неуд"
