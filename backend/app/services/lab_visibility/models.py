"""Модели данных для сервиса видимости лаб."""

from dataclasses import dataclass
from datetime import date


@dataclass
class LabVisibilityInfo:
    """Информация о видимости и дедлайнах лабы для студента."""

    lab_number: int
    is_visible: bool
    visible_from: date | None = None
    deadline_active_from: date | None = None
    lessons_since_activation: int = 0
    deadline_5_status: str | None = None  # 'active', 'expired', None
    deadline_4_status: str | None = None
    lessons_until_deadline_5: int | None = None
    lessons_until_deadline_4: int | None = None
    current_max_grade: int = 5  # Текущий максимальный балл с учётом дедлайна
    lesson_index: int = 0  # Traceable index относительно origin slot
    has_extension: bool = False  # Есть ли активное продление
    extension_bonus: int = 0  # Сколько бонусных пар от продления
    is_excused_origin: bool = False  # Студент был EXCUSED на origin lab slot
    effective_deadline_5_date: date | None = None
    effective_deadline_4_date: date | None = None
