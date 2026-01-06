"""
Утилиты для работы с семестрами.

Семестр 1: сентябрь - декабрь
Семестр 2: январь - май
"""
from datetime import date
from typing import Tuple


def get_current_semester() -> Tuple[int, int]:
    """
    Определить текущий семестр.
    
    Returns:
        (учебный_год, номер_семестра)
        учебный_год - год начала учебного года (например 2025 для 2025-2026)
    """
    now = date.today()
    
    if now.month >= 9:  # сентябрь-декабрь → 1 семестр
        return (now.year, 1)
    elif now.month <= 5:  # январь-май → 2 семестр
        return (now.year - 1, 2)  # учебный год начался в прошлом году
    else:  # июнь-август → межсеместровый период, считаем как конец 2 семестра
        return (now.year - 1, 2)


def get_semester_dates(academic_year: int, semester: int) -> Tuple[date, date]:
    """
    Получить даты начала и конца семестра.
    
    Args:
        academic_year: год начала учебного года (например 2025)
        semester: номер семестра (1 или 2)
    
    Returns:
        (дата_начала, дата_конца)
    """
    if semester == 1:
        return (date(academic_year, 9, 1), date(academic_year, 12, 31))
    else:
        return (date(academic_year + 1, 1, 1), date(academic_year + 1, 5, 31))


def get_academic_year_string(academic_year: int) -> str:
    """
    Получить строку учебного года.
    
    Args:
        academic_year: год начала (например 2025)
    
    Returns:
        "2025-2026"
    """
    return f"{academic_year}-{academic_year + 1}"


def get_semester_for_date(d: date) -> Tuple[int, int]:
    """
    Определить семестр для конкретной даты.
    
    Args:
        d: дата
    
    Returns:
        (учебный_год, номер_семестра)
    """
    if d.month >= 9:
        return (d.year, 1)
    elif d.month <= 5:
        return (d.year - 1, 2)
    else:
        return (d.year - 1, 2)


def format_semester(academic_year: int, semester: int) -> str:
    """
    Форматировать семестр для отображения.
    
    Returns:
        "1 семестр 2025-2026" или "2 семестр 2025-2026"
    """
    return f"{semester} семестр {get_academic_year_string(academic_year)}"
