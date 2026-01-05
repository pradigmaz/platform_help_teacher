"""
Dataclass'ы для результатов расчёта аттестации.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class WorkScoreResult:
    """Результат расчёта баллов за работы (контрольные/самостоятельные/коллоквиумы/проект)"""
    raw_score: float
    weighted_score: float
    count: int
    max_count: int
    submissions_details: List[dict]


@dataclass
class LabScoreResult:
    """Результат расчёта баллов за лабораторные работы"""
    raw_score: float
    weighted_score: float
    labs_count: int
    required_count: int
    bonus_points: float
    submissions_details: List[dict]


@dataclass
class AttendanceScoreResult:
    """Результат расчёта баллов за посещаемость"""
    raw_score: float
    weighted_score: float
    total_classes: int
    present_count: int
    late_count: int
    excused_count: int
    absent_count: int
