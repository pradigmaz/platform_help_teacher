"""
Сервис расчёта видимости лаб и дедлайнов по расписанию.

Правила:
- Видимость лабы = MIN(date) занятий с work_number = N для группы/подгруппы
- Активация дедлайна = MAX(date) занятий с work_number = N
- Дедлайн на 5/4 = N уникальных work_number после активации (не занятий!)
- Продления (LabDeadlineExtension) добавляют bonus_lessons к дедлайнам
"""

from app.services.lab_visibility.models import LabVisibilityInfo
from app.services.lab_visibility.service import LabVisibilityService

__all__ = ["LabVisibilityInfo", "LabVisibilityService"]
