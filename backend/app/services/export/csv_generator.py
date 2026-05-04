"""Генератор CSV файлов для экспорта журнала."""

import csv
import logging
from io import StringIO

from app.schemas.export import JournalExportData
from app.services.export.grade_columns import grade_column_label, grade_work_keys

logger = logging.getLogger(__name__)

# Разделитель для Excel
CSV_DELIMITER = ";"


def generate_attendance_csv(data: JournalExportData) -> str:
    """
    Генерирует CSV с посещаемостью.

    Args:
        data: Данные журнала для экспорта

    Returns:
        CSV строка с посещаемостью
    """
    output = StringIO()
    writer = csv.writer(output, delimiter=CSV_DELIMITER)

    # Заголовки
    headers = ["ФИО", "Подгруппа"]

    # Собираем ключи занятий
    lesson_keys = []
    for lesson in data.lessons:
        col_header = f"{lesson.date.strftime('%d.%m')} №{lesson.lesson_number}"
        headers.append(col_header)
        lesson_keys.append(f"{lesson.date}_{lesson.lesson_number}")

    headers.extend(["Всего", "%"])
    writer.writerow(headers)

    # Символы для статусов
    status_symbols = {
        "PRESENT": "+",
        "LATE": "О",
        "EXCUSED": "У",
        "ABSENT": "Н",
    }

    # Данные студентов
    for row_data in data.attendance_rows:
        row = [
            row_data.student_name,
            row_data.subgroup if row_data.subgroup else "",
        ]

        # Посещаемость по занятиям
        for key in lesson_keys:
            status = row_data.attendance_by_date.get(key, "")
            symbol = status_symbols.get(status, "")
            row.append(symbol)

        # Статистика
        row.append(row_data.stats.get("total", 0))
        row.append(f"{row_data.attendance_rate:.1f}")

        writer.writerow(row)

    logger.debug("CSV посещаемости: %d строк", len(data.attendance_rows))
    return output.getvalue()


def generate_grades_csv(data: JournalExportData) -> str:
    """
    Генерирует CSV с оценками.

    Args:
        data: Данные журнала для экспорта

    Returns:
        CSV строка с оценками
    """
    output = StringIO()
    writer = csv.writer(output, delimiter=CSV_DELIMITER)

    # Заголовки
    headers = ["ФИО", "Подгруппа"]

    sorted_work_keys = grade_work_keys(data)
    headers.extend(grade_column_label(key, multiline=False) for key in sorted_work_keys)
    headers.append("Кол-во")
    writer.writerow(headers)

    # Данные студентов
    for row_data in data.grade_rows:
        row = [
            row_data.student_name,
            row_data.subgroup if row_data.subgroup else "",
        ]

        # Оценки по работам
        for key in sorted_work_keys:
            grade = row_data.grades_by_work.get(key)
            row.append(grade if grade else "")

        # Статистика
        row.append(row_data.grades_count)

        writer.writerow(row)

    logger.debug("CSV оценок: %d строк", len(data.grade_rows))
    return output.getvalue()


def generate_csv(
    data: JournalExportData,
    include_attendance: bool = True,
    include_grades: bool = True,
) -> str:
    """
    Генерирует объединённый CSV файл.

    Args:
        data: Данные журнала для экспорта
        include_attendance: Включить посещаемость
        include_grades: Включить оценки

    Returns:
        CSV строка с данными
    """
    logger.info(
        "Генерация CSV: группа=%s, attendance=%s, grades=%s", data.meta.group_code, include_attendance, include_grades
    )

    sections = []

    # Метаданные
    meta_section = StringIO()
    meta_writer = csv.writer(meta_section, delimiter=CSV_DELIMITER)
    meta_writer.writerow(["Группа", data.meta.group_code])
    meta_writer.writerow(
        ["Период", f"{data.meta.period_start.strftime('%d.%m.%Y')} - {data.meta.period_end.strftime('%d.%m.%Y')}"]
    )
    meta_writer.writerow(["Студентов", data.meta.total_students])
    meta_writer.writerow(["Занятий", data.meta.total_lessons])
    sections.append(meta_section.getvalue())

    # Посещаемость
    if include_attendance and data.attendance_rows:
        sections.append("")  # Пустая строка-разделитель
        sections.append("ПОСЕЩАЕМОСТЬ")
        sections.append(generate_attendance_csv(data))

    # Оценки
    if include_grades and data.grade_rows:
        sections.append("")  # Пустая строка-разделитель
        sections.append("ОЦЕНКИ")
        sections.append(generate_grades_csv(data))

    result = "\n".join(sections)
    logger.info("CSV файл сгенерирован: %d символов", len(result))
    return result
