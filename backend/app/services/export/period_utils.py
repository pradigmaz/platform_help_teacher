"""Утилиты парсинга периодов для экспорта журнала."""

import calendar
import logging
from datetime import date, datetime, timedelta

from app.schemas.export import ExportPeriodType
from app.utils.semester import get_current_semester, get_semester_dates

logger = logging.getLogger(__name__)


def parse_day(value: str) -> tuple[date, date]:
    """
    Парсинг дня.

    Args:
        value: Дата в формате "YYYY-MM-DD"

    Returns:
        (start_date, end_date) — одна и та же дата

    Raises:
        ValueError: Неверный формат даты
    """
    try:
        d = datetime.strptime(value, "%Y-%m-%d").date()
        return (d, d)
    except ValueError as e:
        logger.error(f"Ошибка парсинга дня '{value}': {e}")
        raise ValueError(
            f"Неверный формат даты '{value}'. Ожидается формат YYYY-MM-DD (например, 2025-01-22)"
        ) from e


def parse_week(value: str) -> tuple[date, date]:
    """
    Парсинг ISO недели.

    Args:
        value: Неделя в формате "YYYY-Www" (например, "2025-W04")

    Returns:
        (понедельник, воскресенье) указанной недели

    Raises:
        ValueError: Неверный формат недели
    """
    try:
        # %G — ISO год, %V — ISO номер недели, %u — день недели (1=пн)
        monday = datetime.strptime(f"{value}-1", "%G-W%V-%u").date()
        sunday = monday + timedelta(days=6)
        return (monday, sunday)
    except ValueError as e:
        logger.error(f"Ошибка парсинга недели '{value}': {e}")
        raise ValueError(
            f"Неверный формат недели '{value}'. Ожидается формат YYYY-Www (например, 2025-W04)"
        ) from e


def parse_month(value: str) -> tuple[date, date]:
    """
    Парсинг месяца.

    Args:
        value: Месяц в формате "YYYY-MM" (например, "2025-01")

    Returns:
        (первый день месяца, последний день месяца)

    Raises:
        ValueError: Неверный формат месяца
    """
    try:
        first_day = datetime.strptime(f"{value}-01", "%Y-%m-%d").date()
        _, last_day_num = calendar.monthrange(first_day.year, first_day.month)
        last_day = date(first_day.year, first_day.month, last_day_num)
        return (first_day, last_day)
    except ValueError as e:
        logger.error(f"Ошибка парсинга месяца '{value}': {e}")
        raise ValueError(
            f"Неверный формат месяца '{value}'. Ожидается формат YYYY-MM (например, 2025-01)"
        ) from e


def parse_custom(value: str) -> tuple[date, date]:
    """
    Парсинг произвольного периода.

    Args:
        value: Период в формате "YYYY-MM-DD:YYYY-MM-DD" (например, "2025-01-01:2025-01-31")

    Returns:
        (start_date, end_date)

    Raises:
        ValueError: Неверный формат периода или start > end
    """
    if ":" not in value:
        raise ValueError(
            f"Неверный формат периода '{value}'. "
            "Ожидается формат YYYY-MM-DD:YYYY-MM-DD (например, 2025-01-01:2025-01-31)"
        )

    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError(
            f"Неверный формат периода '{value}'. "
            "Должно быть ровно две даты, разделённые двоеточием"
        )

    try:
        start_date = datetime.strptime(parts[0], "%Y-%m-%d").date()
        end_date = datetime.strptime(parts[1], "%Y-%m-%d").date()
    except ValueError as e:
        logger.error(f"Ошибка парсинга дат в периоде '{value}': {e}")
        raise ValueError(
            f"Неверный формат дат в периоде '{value}'. "
            "Ожидается формат YYYY-MM-DD:YYYY-MM-DD"
        ) from e

    if start_date > end_date:
        raise ValueError(
            f"Дата начала ({start_date}) не может быть позже даты окончания ({end_date})"
        )

    return (start_date, end_date)


def parse_period(
    period_type: ExportPeriodType,
    period_value: str | None = None,
) -> tuple[date, date]:
    """
    Парсинг периода в даты начала и конца.

    Args:
        period_type: Тип периода (day/week/month/semester/custom)
        period_value: Значение периода (не нужно для semester)

    Returns:
        (start_date, end_date)

    Raises:
        ValueError: Неверный формат period_value или отсутствует обязательное значение

    Примеры:
        >>> parse_period(ExportPeriodType.DAY, "2025-01-22")
        (date(2025, 1, 22), date(2025, 1, 22))

        >>> parse_period(ExportPeriodType.WEEK, "2025-W04")
        (date(2025, 1, 20), date(2025, 1, 26))

        >>> parse_period(ExportPeriodType.MONTH, "2025-01")
        (date(2025, 1, 1), date(2025, 1, 31))

        >>> parse_period(ExportPeriodType.SEMESTER)
        # Возвращает даты текущего семестра

        >>> parse_period(ExportPeriodType.CUSTOM, "2025-01-01:2025-01-31")
        (date(2025, 1, 1), date(2025, 1, 31))
    """
    logger.debug(f"Парсинг периода: type={period_type}, value={period_value}")

    if period_type == ExportPeriodType.SEMESTER:
        academic_year, semester = get_current_semester()
        start_date, end_date = get_semester_dates(academic_year, semester)
        logger.info(
            f"Период семестра: {semester} семестр {academic_year}-{academic_year + 1}, "
            f"даты: {start_date} — {end_date}"
        )
        return (start_date, end_date)

    # Для остальных типов period_value обязателен
    if not period_value:
        raise ValueError(
            f"Для типа периода '{period_type.value}' необходимо указать period_value"
        )

    if period_type == ExportPeriodType.DAY:
        return parse_day(period_value)

    if period_type == ExportPeriodType.WEEK:
        return parse_week(period_value)

    if period_type == ExportPeriodType.MONTH:
        return parse_month(period_value)

    if period_type == ExportPeriodType.CUSTOM:
        return parse_custom(period_value)

    # На случай добавления новых типов
    raise ValueError(f"Неизвестный тип периода: {period_type}")
