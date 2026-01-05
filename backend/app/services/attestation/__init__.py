"""
Модуль аттестации - расчёт баллов и управление настройками.

Структура:
- calculator.py - калькулятор баллов (чистая логика расчёта)
- models.py - dataclass'ы для результатов расчёта
- service.py - сервис для работы с БД и оркестрация расчётов
"""
from .service import AttestationService
from .calculator import AttestationCalculator
from .models import LabScoreResult, AttendanceScoreResult, WorkScoreResult

__all__ = [
    "AttestationService",
    "AttestationCalculator",
    "LabScoreResult",
    "AttendanceScoreResult",
    "WorkScoreResult",
]
