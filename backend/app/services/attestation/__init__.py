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
from .service import AttestationService
from .calculator import AttestationCalculator
from .lab_calculator import LabScoreResult, LabScoreCalculator
from .attendance_calculator import AttendanceScoreResult, AttendanceScoreCalculator
from .settings import AttestationSettingsManager
from .student_score import StudentScoreCalculator
from .batch import BatchScoreCalculator

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
