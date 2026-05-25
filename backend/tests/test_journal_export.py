"""Тесты экспорта журнала."""
import pytest
from datetime import date, datetime, timezone
from uuid import uuid4

from app.schemas.export import (
    ExportPeriodType,
    JournalExportData,
    JournalExportMeta,
    AttendanceExportRow,
    GradeExportRow,
    LessonExportColumn,
)
from app.services.export.period_utils import (
    parse_period,
    parse_day,
    parse_week,
    parse_month,
    parse_custom,
)
from app.services.export.attendance_helpers import (
    filter_lessons_for_subgroup,
    filter_students_for_export,
    filter_students_for_subgroup,
    resolve_export_subgroup,
)
from app.api.v1.endpoints.journal.export import build_content_disposition_header
from app.services.export.excel_generator import generate_excel
from app.services.export.csv_generator import generate_csv


class TestPeriodParsing:
    """Тесты парсинга периодов."""

    def test_parse_day(self):
        """Парсинг дня."""
        start, end = parse_day("2025-01-22")
        assert start == date(2025, 1, 22)
        assert end == date(2025, 1, 22)

    def test_parse_day_invalid(self):
        """Неверный формат дня."""
        with pytest.raises(ValueError):
            parse_day("22-01-2025")

    def test_parse_day_invalid_format(self):
        """Неверный формат дня — буквы."""
        with pytest.raises(ValueError):
            parse_day("invalid")

    def test_parse_week(self):
        """Парсинг ISO недели."""
        start, end = parse_week("2025-W04")
        assert start.weekday() == 0  # Понедельник
        assert (end - start).days == 6  # Воскресенье

    def test_parse_week_first_week(self):
        """Парсинг первой недели года."""
        start, end = parse_week("2025-W01")
        assert start.weekday() == 0
        assert (end - start).days == 6

    def test_parse_week_invalid(self):
        """Неверный формат недели."""
        with pytest.raises(ValueError):
            parse_week("2025-04")

    def test_parse_week_invalid_format(self):
        """Неверный формат недели — без W."""
        with pytest.raises(ValueError):
            parse_week("202504")

    def test_parse_month(self):
        """Парсинг месяца."""
        start, end = parse_month("2025-01")
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)

    def test_parse_month_february(self):
        """Парсинг февраля (28/29 дней)."""
        start, end = parse_month("2024-02")  # Високосный
        assert end == date(2024, 2, 29)

    def test_parse_month_february_non_leap(self):
        """Парсинг февраля невисокосного года."""
        start, end = parse_month("2025-02")
        assert end == date(2025, 2, 28)

    def test_parse_month_invalid(self):
        """Неверный формат месяца."""
        with pytest.raises(ValueError):
            parse_month("2025/01")

    def test_parse_custom(self):
        """Парсинг произвольного периода."""
        start, end = parse_custom("2025-01-01:2025-01-31")
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)

    def test_parse_custom_same_day(self):
        """Парсинг периода в один день."""
        start, end = parse_custom("2025-01-15:2025-01-15")
        assert start == end == date(2025, 1, 15)

    def test_parse_custom_invalid_order(self):
        """Начало позже конца."""
        with pytest.raises(ValueError):
            parse_custom("2025-01-31:2025-01-01")

    def test_parse_custom_no_separator(self):
        """Отсутствует разделитель."""
        with pytest.raises(ValueError):
            parse_custom("2025-01-01")

    def test_parse_custom_invalid_dates(self):
        """Неверный формат дат."""
        with pytest.raises(ValueError):
            parse_custom("01-01-2025:31-01-2025")

    def test_parse_period_semester(self):
        """Парсинг семестра."""
        start, end = parse_period(ExportPeriodType.SEMESTER)
        assert start < end
        # Семестр должен быть в пределах учебного года

    def test_parse_period_day(self):
        """Парсинг периода день."""
        start, end = parse_period(ExportPeriodType.DAY, "2025-01-22")
        assert start == end == date(2025, 1, 22)

    def test_parse_period_week(self):
        """Парсинг периода неделя."""
        start, end = parse_period(ExportPeriodType.WEEK, "2025-W04")
        assert start.weekday() == 0
        assert (end - start).days == 6

    def test_parse_period_month(self):
        """Парсинг периода месяц."""
        start, end = parse_period(ExportPeriodType.MONTH, "2025-01")
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)

    def test_parse_period_custom(self):
        """Парсинг произвольного периода."""
        start, end = parse_period(ExportPeriodType.CUSTOM, "2025-01-01:2025-01-31")
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)

    def test_parse_period_missing_value(self):
        """Отсутствует period_value для не-семестра."""
        with pytest.raises(ValueError):
            parse_period(ExportPeriodType.DAY, None)

    def test_parse_period_missing_value_week(self):
        """Отсутствует period_value для недели."""
        with pytest.raises(ValueError):
            parse_period(ExportPeriodType.WEEK, None)


def _create_test_meta() -> JournalExportMeta:
    """Создаёт тестовые метаданные."""
    return JournalExportMeta(
        group_code="TEST-01",
        group_name="Тестовая группа",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 1, 31),
        generated_at=datetime.now(timezone.utc),
        total_students=0,
        total_lessons=0,
    )


def _create_test_data_empty() -> JournalExportData:
    """Создаёт пустые тестовые данные."""
    return JournalExportData(
        meta=_create_test_meta(),
        lessons=[],
        attendance_rows=[],
        grade_rows=[],
    )


def _create_test_data_with_students() -> JournalExportData:
    """Создаёт тестовые данные со студентами."""
    meta = JournalExportMeta(
        group_code="TEST-01",
        group_name="Тестовая группа",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 1, 31),
        generated_at=datetime.now(timezone.utc),
        total_students=2,
        total_lessons=3,
    )

    lessons = [
        LessonExportColumn(
            lesson_id=uuid4(),
            date=date(2025, 1, 10),
            lesson_number=1,
            lesson_type="lecture",
            topic="Введение",
        ),
        LessonExportColumn(
            lesson_id=uuid4(),
            date=date(2025, 1, 17),
            lesson_number=1,
            lesson_type="lab",
            topic="Лаба 1",
            work_number=1,
        ),
        LessonExportColumn(
            lesson_id=uuid4(),
            date=date(2025, 1, 24),
            lesson_number=1,
            lesson_type="practice",
            topic="Практика 1",
        ),
    ]

    attendance_rows = [
        AttendanceExportRow(
            student_id=uuid4(),
            student_name="Иванов Иван Иванович",
            subgroup=1,
            attendance_by_date={
                "2025-01-10_1": "PRESENT",
                "2025-01-17_1": "ABSENT",
                "2025-01-24_1": "LATE",
            },
            stats={
                "total": 3,
                "present_count": 1,
                "absent_count": 1,
                "late_count": 1,
                "excused_count": 0,
            },
            attendance_rate=66.7,
        ),
        AttendanceExportRow(
            student_id=uuid4(),
            student_name="Петров Пётр Петрович",
            subgroup=2,
            attendance_by_date={
                "2025-01-10_1": "PRESENT",
                "2025-01-17_1": "PRESENT",
                "2025-01-24_1": "EXCUSED",
            },
            stats={
                "total": 3,
                "present_count": 2,
                "absent_count": 0,
                "late_count": 0,
                "excused_count": 1,
            },
            attendance_rate=100.0,
        ),
    ]

    grade_rows = [
        GradeExportRow(
            student_id=attendance_rows[0].student_id,
            student_name="Иванов Иван Иванович",
            subgroup=1,
            grades_by_work={"2025-01-17_1_1": 4},
            average_grade=4.0,
            grades_count=1,
        ),
        GradeExportRow(
            student_id=attendance_rows[1].student_id,
            student_name="Петров Пётр Петрович",
            subgroup=2,
            grades_by_work={"2025-01-17_1_1": 5},
            average_grade=5.0,
            grades_count=1,
        ),
    ]

    return JournalExportData(
        meta=meta,
        lessons=lessons,
        attendance_rows=attendance_rows,
        grade_rows=grade_rows,
    )


class TestExcelGeneration:
    """Тесты генерации Excel."""

    def test_generate_excel_empty_data(self):
        """Генерация Excel с пустыми данными."""
        data = _create_test_data_empty()
        result = generate_excel(data)

        assert isinstance(result, bytes)
        assert len(result) > 0
        # Проверяем сигнатуру xlsx (PK zip)
        assert result[:2] == b"PK"

    def test_generate_excel_with_students(self):
        """Генерация Excel с данными студентов."""
        data = _create_test_data_with_students()
        result = generate_excel(data)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:2] == b"PK"

    def test_generate_excel_only_attendance(self):
        """Генерация Excel только с посещаемостью."""
        data = _create_test_data_with_students()
        data.grade_rows = []
        result = generate_excel(data)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_excel_only_grades(self):
        """Генерация Excel только с оценками."""
        data = _create_test_data_with_students()
        data.attendance_rows = []
        result = generate_excel(data)

        assert isinstance(result, bytes)
        assert len(result) > 0


class TestSubgroupFiltering:
    """Тесты фильтрации экспорта по подгруппе."""

    def test_filter_students_for_subgroup_keeps_only_matching_students(self):
        student_a = type("Student", (), {"subgroup": 1})()
        student_b = type("Student", (), {"subgroup": 2})()
        student_c = type("Student", (), {"subgroup": None})()

        result = filter_students_for_subgroup([student_a, student_b, student_c], 1)

        assert result == [student_a]

    def test_filter_lessons_for_subgroup_keeps_common_and_matching_lessons(self):
        lecture = type("Lesson", (), {"subgroup": None})()
        subgroup_one = type("Lesson", (), {"subgroup": 1})()
        subgroup_two = type("Lesson", (), {"subgroup": 2})()

        result = filter_lessons_for_subgroup([lecture, subgroup_one, subgroup_two], 1)

        assert result == [lecture, subgroup_one]

    def test_filter_students_for_export_keeps_only_selected_student(self):
        student_id = uuid4()
        selected_student = type("Student", (), {"id": student_id, "subgroup": 1})()
        another_student = type("Student", (), {"id": uuid4(), "subgroup": 1})()

        result = filter_students_for_export(
            [selected_student, another_student],
            subgroup=None,
            student_id=student_id,
        )

        assert result == [selected_student]

    def test_resolve_export_subgroup_uses_single_student_subgroup(self):
        student = type("Student", (), {"subgroup": 2})()

        result = resolve_export_subgroup([student], subgroup=None, student_id=uuid4())

        assert result == 2

    def test_resolve_export_subgroup_respects_explicit_subgroup(self):
        student = type("Student", (), {"subgroup": 2})()

        result = resolve_export_subgroup([student], subgroup=1, student_id=uuid4())

        assert result == 1

    def test_resolve_export_subgroup_does_not_narrow_whole_group_export(self):
        student = type("Student", (), {"subgroup": 2})()

        result = resolve_export_subgroup([student], subgroup=None, student_id=None)

        assert result is None


class TestContentDispositionHeader:
    """Тесты заголовка скачивания файлов."""

    def test_build_content_disposition_header_supports_unicode_filename(self):
        header = build_content_disposition_header("journal_ИС1231ОТ_2026-01-01_2026-05-31.xlsx")

        assert 'filename="journal_1231_2026-01-01_2026-05-31.xlsx"' in header
        assert "filename*=UTF-8''journal_%D0%98%D0%A11231%D0%9E%D0%A2_2026-01-01_2026-05-31.xlsx" in header


class TestCsvGeneration:
    """Тесты генерации CSV."""

    def test_generate_csv_empty_data(self):
        """Генерация CSV с пустыми данными."""
        data = _create_test_data_empty()
        result = generate_csv(data, include_attendance=True, include_grades=True)

        assert isinstance(result, str)
        assert "TEST-01" in result
        assert "Группа" in result

    def test_generate_csv_with_students(self):
        """Генерация CSV с данными студентов."""
        data = _create_test_data_with_students()
        result = generate_csv(data, include_attendance=True, include_grades=True)

        assert isinstance(result, str)
        assert "TEST-01" in result
        assert "Иванов" in result
        assert "Петров" in result
        assert "ПОСЕЩАЕМОСТЬ" in result
        assert "ОЦЕНКИ" in result

    def test_generate_csv_only_attendance(self):
        """Генерация CSV только с посещаемостью."""
        data = _create_test_data_with_students()
        result = generate_csv(data, include_attendance=True, include_grades=False)

        assert isinstance(result, str)
        assert "ПОСЕЩАЕМОСТЬ" in result
        assert "ОЦЕНКИ" not in result

    def test_generate_csv_only_grades(self):
        """Генерация CSV только с оценками."""
        data = _create_test_data_with_students()
        result = generate_csv(data, include_attendance=False, include_grades=True)

        assert isinstance(result, str)
        assert "ПОСЕЩАЕМОСТЬ" not in result
        assert "ОЦЕНКИ" in result

    def test_generate_csv_neither(self):
        """Генерация CSV без данных (только мета)."""
        data = _create_test_data_with_students()
        result = generate_csv(data, include_attendance=False, include_grades=False)

        assert isinstance(result, str)
        assert "TEST-01" in result
        # Только метаданные
        assert "ПОСЕЩАЕМОСТЬ" not in result
        assert "ОЦЕНКИ" not in result
