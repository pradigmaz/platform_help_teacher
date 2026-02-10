"""
Модуль аттестации - автобалансировка баллов.

Структура:
- calculator.py - фасад калькуляторов
- lab_calculator.py - расчёт баллов за лабораторные
- attendance_calculator.py - расчёт баллов за посещаемость
- settings.py - управление настройками
- student_score.py - расчёт для одного студента
- batch.py - пакетные операции
- service.py - фасад модуля
"""

from .attendance_calculator import AttendanceScoreCalculator, AttendanceScoreResult
from .batch import BatchScoreCalculator
from .calculator import AttestationCalculator
from .lab_calculator import LabScoreCalculator, LabScoreResult
from .service import AttestationService
from .settings import AttestationSettingsManager
from .student_score import StudentScoreCalculator

__all__ = [
    "AttestationService",
    "AttestationCalculator",
    "AttestationSettingsManager",
    "StudentScoreCalculator",
    "BatchScoreCalculator",
    "LabScoreResult",
    "LabScoreCalculator",
    "AttendanceScoreResult",
    "AttendanceScoreCalculator",
]
