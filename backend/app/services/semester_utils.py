"""
Утилиты для работы с семестрами
"""
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.services.html_parser import ParsedLesson
from app.services.schedule_constants import SEMESTER_END_EMPTY_WEEKS_THRESHOLD


def get_semester(d: date) -> str:
    """Определить семестр по дате"""
    year = d.year
    if d.month >= 9:
        return f"{year}-1"
    elif d.month <= 1:
        return f"{year-1}-1"
    else:
        return f"{year}-2"


def detect_semester_end(parsed_lessons: list[ParsedLesson], start_date: date, end_date: date) -> dict:
    """
    Автоопределение конца семестра.
    
    Если после активного периода идут 2+ пустые недели подряд — 
    считаем что семестр закончился.
    
    Returns:
        {
            "detected": bool,
            "last_lesson_date": str | None,
            "empty_weeks": int
        }
    """
    if not parsed_lessons:
        return {"detected": False, "last_lesson_date": None, "empty_weeks": 0}
    
    lesson_dates = sorted(set(p.date for p in parsed_lessons))
    
    if not lesson_dates:
        return {"detected": False, "last_lesson_date": None, "empty_weeks": 0}
    
    last_lesson_date = lesson_dates[-1]
    
    days_after_last = (end_date - last_lesson_date).days
    empty_weeks = days_after_last // 7
    
    # Если 2+ пустых недели после последнего занятия — конец семестра
    if empty_weeks >= SEMESTER_END_EMPTY_WEEKS_THRESHOLD:
        return {
            "detected": True,
            "last_lesson_date": last_lesson_date.isoformat(),
            "empty_weeks": empty_weeks
        }
    
    return {
        "detected": False, 
        "last_lesson_date": last_lesson_date.isoformat(), 
        "empty_weeks": empty_weeks
    }


async def find_teacher(db: AsyncSession, teacher_name: str) -> Optional[User]:
    """Найти преподавателя по имени"""
    result = await db.execute(
        select(User).where(
            User.full_name == teacher_name,
            User.role == UserRole.TEACHER
        )
    )
    return result.scalar_one_or_none()
