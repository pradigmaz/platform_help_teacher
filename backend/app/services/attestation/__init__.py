"""
Модуль аттестации - расчёт баллов и управление настройками.

Структура:
- constants.py - константы (MIN_GRADE, MAX_GRADE, etc.)
- models.py - dataclass'ы для результатов расчёта
- lab_calculator.py - расчёт баллов за лабораторные
- attendance_calculator.py - расчёт баллов за посещаемость
- work_calculator.py - расчёт баллов за работы
- calculator.py - фасад калькуляторов
- settings.py - управление настройками аттестации
- student_score.py - расчёт баллов для одного студента
- batch.py - пакетные операции расчёта
- service.py - фасад для всех модулей
"""
from .service import AttestationService
from .calculator import AttestationCalculator
from .models import LabScoreResult, AttendanceScoreResult, WorkScoreResult
from .settings import AttestationSettingsManager, DEFAULT_SETTINGS
from .student_score import StudentScoreCalculator
from .batch import BatchScoreCalculator
from .constants import MIN_GRADE, MAX_GRADE, GRADE_RANGE

__all__ = [
    "AttestationService",
    "AttestationCalculator",
    "AttestationSettingsManager",
    "StudentScoreCalculator",
    "BatchScoreCalculator",
    "LabScoreResult",
    "AttendanceScoreResult",
    "WorkScoreResult",
    "DEFAULT_SETTINGS",
    "MIN_GRADE",
    "MAX_GRADE",
    "GRADE_RANGE",
]
