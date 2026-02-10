"""
Вспомогательные функции для модуля аттестации.
"""

from sqlalchemy import or_
from sqlalchemy.sql import Select

from app.models.lesson import Lesson


def filter_lessons_by_subgroup(
    query: Select,
    student_subgroup: int | None
) -> Select:
    """
    Фильтрация занятий по подгруппе студента.

    Логика:
    - Если студент в подгруппе: показываем общие занятия (subgroup=None) + его подгруппу
    - Если студент без подгруппы: показываем только общие занятия

    Args:
        query: SQLAlchemy Select запрос с Lesson
        student_subgroup: Номер подгруппы студента или None

    Returns:
        Отфильтрованный запрос
    """
    if student_subgroup is not None:
        return query.where(
            or_(Lesson.subgroup.is_(None), Lesson.subgroup == student_subgroup)
        )
    else:
        return query.where(Lesson.subgroup.is_(None))
