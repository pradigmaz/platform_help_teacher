from datetime import date

from app.services.lab_grade_import.parser import parse_grade_notes


def test_parse_normalized_notes_expands_ranges(tmp_path):
    notes = tmp_path / "grades.md"
    notes.write_text(
        """
# Журнал

## 20.03.2026

### Группа 235

- Висягина - 5(5-10)
- Бурёнкина - 5-10 (5), нужен формат записи
""",
        encoding="utf-8",
    )

    entries = parse_grade_notes(notes)

    assert [(entry.student_label, entry.grade, entry.work_number) for entry in entries] == [
        ("Висягина", 5, 5),
        ("Висягина", 5, 6),
        ("Висягина", 5, 7),
        ("Висягина", 5, 8),
        ("Висягина", 5, 9),
        ("Висягина", 5, 10),
        ("Бурёнкина", 5, 5),
        ("Бурёнкина", 5, 6),
        ("Бурёнкина", 5, 7),
        ("Бурёнкина", 5, 8),
        ("Бурёнкина", 5, 9),
        ("Бурёнкина", 5, 10),
    ]
    assert {entry.group_label for entry in entries} == {"235"}
    assert {entry.source_date for entry in entries} == {date(2026, 3, 20)}


def test_parse_raw_notes_uses_inline_groups_and_multiple_grades(tmp_path):
    notes = tmp_path / "grades.md"
    notes.write_text(
        """
15.04.2026

237

Меньшикова - 4(6), 5(7)

Боброва 238 - 4(7), 5(8)
""",
        encoding="utf-8",
    )

    entries = parse_grade_notes(notes)

    assert [(entry.group_label, entry.student_label, entry.grade, entry.work_number) for entry in entries] == [
        ("237", "Меньшикова", 4, 6),
        ("237", "Меньшикова", 5, 7),
        ("238", "Боброва", 4, 7),
        ("238", "Боброва", 5, 8),
    ]


def test_parse_skips_lines_without_grades_or_groups(tmp_path):
    notes = tmp_path / "grades.md"
    notes.write_text(
        """
## Нужна проверка
- 25.03.2026, группа 234: у Барсукова не указана оценка.

## 13.03.2026

### Без указанной группы

- Пьянков - 3
- Чернышов - без оценки
""",
        encoding="utf-8",
    )

    assert parse_grade_notes(notes) == []
