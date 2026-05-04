"""Helpers for journal export grade columns."""

from app.schemas.export import JournalExportData


def grade_work_key(date_value, lesson_number: int, work_number: int | None) -> str:
    work_num = work_number if work_number else 0
    return f"{date_value}_{lesson_number}_{work_num}"


def grade_column_label(key: str, *, multiline: bool) -> str:
    date_str, lesson_number, work_number = key.split("_", 2)
    try:
        from datetime import datetime

        label = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m")
    except ValueError:
        label = date_str
    suffix = f"№{lesson_number}"
    if work_number != "0":
        separator = "/р" if multiline else " р"
        suffix = f"{suffix}{separator}{work_number}"
    joiner = "\n" if multiline else " "
    return f"{label}{joiner}{suffix}"


def grade_work_keys(data: JournalExportData) -> list[str]:
    work_keys = {grade_work_key(lesson.date, lesson.lesson_number, lesson.work_number) for lesson in data.lessons}
    for row_data in data.grade_rows:
        work_keys.update(row_data.grades_by_work.keys())
    return sorted(work_keys)


def grade_lesson_subgroups(data: JournalExportData) -> dict[str, int | None]:
    return {
        grade_work_key(lesson.date, lesson.lesson_number, lesson.work_number): lesson.subgroup
        for lesson in data.lessons
    }


def is_other_subgroup_lesson(lesson_subgroup: int | None, student_subgroup: int | None) -> bool:
    return lesson_subgroup is not None and student_subgroup != lesson_subgroup
