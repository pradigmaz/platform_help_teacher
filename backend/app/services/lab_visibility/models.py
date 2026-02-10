"""Модели данных для сервиса видимости лаб."""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class LabVisibilityInfo:
    """Информация о видимости и дедлайнах лабы для студента."""
    lab_number: int
    is_visible: bool
    visible_from: Optional[date] = None
    deadline_active_from: Optional[date] = None
    lessons_since_activation: int = 0
    deadline_5_status: Optional[str] = None  # 'active', 'expired', None
    deadline_4_status: Optional[str] = None
    lessons_until_deadline_5: Optional[int] = None
    lessons_until_deadline_4: Optional[int] = None
    current_max_grade: int = 5  # Текущий максимальный балл с учётом дедлайна
    has_extension: bool = False  # Есть ли активное продление
    extension_bonus: int = 0  # Сколько бонусных пар от продления
