"""
Тесты для модуля Journal (оценки и посещаемость).
"""

from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models import Attendance, AttendanceStatus, Group, Lesson, LessonGrade, User
from app.models.schedule import LessonType
from app.models.user import UserRole
from app.schemas.lesson_grade import (
    AttendanceRecord,
    BulkAttendanceUpdate,
    BulkGradeCreate,
    GradeItem,
    LessonGradeCreate,
    LessonGradeUpdate,
)
from app.schemas.schedule import GroupedLectureSheetSaveItem, GroupedLectureSheetSaveRequest, LessonSheetSaveRequest
from app.services.grade_cell_summary import summarize_lesson_grade_cell
from app.services.journal_grade_service import (
    JournalGradeConflictError,
    JournalGradeValidationError,
    JournalGradeWriteService,
)
from app.services.lesson_sheet_service import LessonSheetService


class TestGradeValidation:
    """Тесты валидации оценок."""

    def test_create_grade_validation_valid(self):
        """Валидные оценки 2-5 проходят."""
        for grade in [2, 3, 4, 5]:
            item = GradeItem(student_id=uuid4(), grade=grade)
            assert item.grade == grade

    def test_create_grade_validation_invalid_low(self):
        """Оценка < 2 отклоняется."""
        with pytest.raises(ValidationError) as exc_info:
            GradeItem(student_id=uuid4(), grade=1)
        assert "greater than or equal to 2" in str(exc_info.value)

    def test_create_grade_validation_invalid_high(self):
        """Оценка > 5 отклоняется."""
        with pytest.raises(ValidationError) as exc_info:
            GradeItem(student_id=uuid4(), grade=6)
        assert "less than or equal to 5" in str(exc_info.value)

    def test_work_number_validation_valid(self):
        """Валидные номера работ 1-20 проходят."""
        for num in [1, 10, 20]:
            item = GradeItem(student_id=uuid4(), grade=5, work_number=num)
            assert item.work_number == num

    def test_work_number_validation_invalid_low(self):
        """work_number < 1 отклоняется."""
        with pytest.raises(ValidationError) as exc_info:
            GradeItem(student_id=uuid4(), grade=5, work_number=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_work_number_validation_invalid_high(self):
        """work_number > 20 отклоняется."""
        with pytest.raises(ValidationError) as exc_info:
            GradeItem(student_id=uuid4(), grade=5, work_number=21)
        assert "less than or equal to 20" in str(exc_info.value)


class TestBulkAttendanceSchema:
    """Тесты схемы массового обновления посещаемости."""

    def test_bulk_attendance_valid(self):
        """Валидная схема проходит."""
        data = BulkAttendanceUpdate(
            lesson_id=uuid4(),
            records=[
                AttendanceRecord(student_id=uuid4(), status="PRESENT"),
                AttendanceRecord(student_id=uuid4(), status="ABSENT"),
            ],
        )
        assert len(data.records) == 2

    def test_bulk_attendance_empty_records(self):
        """Пустой список записей допустим."""
        data = BulkAttendanceUpdate(lesson_id=uuid4(), records=[])
        assert len(data.records) == 0


class TestBulkGradeSchema:
    """Тесты схемы массового создания оценок."""

    def test_bulk_grade_valid(self):
        """Валидная схема проходит."""
        data = BulkGradeCreate(
            lesson_id=uuid4(),
            grades=[
                GradeItem(student_id=uuid4(), grade=5, work_number=1),
                GradeItem(student_id=uuid4(), grade=4),
            ],
        )
        assert len(data.grades) == 2

    def test_bulk_grade_invalid_grade_in_list(self):
        """Невалидная оценка в списке отклоняется."""
        with pytest.raises(ValidationError):
            BulkGradeCreate(
                lesson_id=uuid4(),
                grades=[
                    GradeItem(student_id=uuid4(), grade=5),
                    GradeItem(student_id=uuid4(), grade=10),  # Invalid
                ],
            )


class TestAttendanceStatusEnum:
    """Тесты enum статусов посещаемости."""

    def test_valid_statuses(self):
        """Все валидные статусы существуют."""
        valid = ["PRESENT", "ABSENT", "LATE", "EXCUSED"]
        for status in valid:
            assert hasattr(AttendanceStatus, status)

    def test_status_values(self):
        """Значения enum корректны."""
        assert AttendanceStatus.PRESENT.value == "PRESENT"
        assert AttendanceStatus.ABSENT.value == "ABSENT"
        assert AttendanceStatus.LATE.value == "LATE"
        assert AttendanceStatus.EXCUSED.value == "EXCUSED"


class TestLessonGradeModel:
    """Тесты модели LessonGrade."""

    def test_model_has_check_constraint(self):
        """Модель имеет CheckConstraint на grade."""
        constraints = [c.name for c in LessonGrade.__table__.constraints if hasattr(c, "name") and c.name]
        assert "ck_lesson_grade_range" in constraints

    def test_model_has_work_number_index(self):
        """Модель имеет индекс на work_number."""
        indexes = [idx.name for idx in LessonGrade.__table__.indexes]
        assert "idx_lesson_grades_work_number" in indexes

    def test_model_has_lesson_student_index(self):
        """Модель имеет составной индекс lesson_id + student_id."""
        indexes = [idx.name for idx in LessonGrade.__table__.indexes]
        assert "idx_lesson_grades_lesson_student" in indexes


class TestGradeCellSummary:
    """Тесты сериализации ячейки журнала."""

    def test_distinct_work_numbers_are_multi_grade_not_conflict(self):
        lesson_id = uuid4()
        student_id = uuid4()
        rows = [
            LessonGrade(lesson_id=lesson_id, student_id=student_id, work_number=10, grade=5),
            LessonGrade(lesson_id=lesson_id, student_id=student_id, work_number=5, grade=4),
        ]

        payload = summarize_lesson_grade_cell(rows)

        assert payload["has_conflict"] is False
        assert payload["conflict_count"] == 0
        assert payload["grade_items"] == [
            {"grade": 4, "work_number": 5},
            {"grade": 5, "work_number": 10},
        ]

    def test_duplicate_work_numbers_stay_conflict(self):
        lesson_id = uuid4()
        student_id = uuid4()
        rows = [
            LessonGrade(lesson_id=lesson_id, student_id=student_id, work_number=5, grade=4),
            LessonGrade(lesson_id=lesson_id, student_id=student_id, work_number=5, grade=5),
        ]

        payload = summarize_lesson_grade_cell(rows)

        assert payload["has_conflict"] is True
        assert payload["grade"] is None
        assert payload["work_number"] is None
        assert payload["conflict_count"] == 2


class TestLessonGradeCreate:
    """Тесты схемы создания оценки."""

    def test_create_schema_valid(self):
        """Валидная схема создания."""
        data = LessonGradeCreate(lesson_id=uuid4(), student_id=uuid4(), grade=5, work_number=1, comment="Отлично")
        assert data.grade == 5
        assert data.work_number == 1

    def test_create_schema_minimal(self):
        """Минимальная схема (только обязательные поля)."""
        data = LessonGradeCreate(lesson_id=uuid4(), student_id=uuid4(), grade=3)
        assert data.grade == 3
        assert data.work_number is None
        assert data.comment is None


class TestLessonGradeUpdate:
    """Тесты схемы обновления оценки."""

    def test_update_schema_partial(self):
        """Частичное обновление (только grade)."""
        data = LessonGradeUpdate(grade=4)
        assert data.grade == 4
        assert data.work_number is None

    def test_update_schema_grade_validation(self):
        """Валидация grade при обновлении."""
        with pytest.raises(ValidationError):
            LessonGradeUpdate(grade=10)


class TestJournalGradeWriteService:
    """Тесты канонического write-path для оценок."""

    @pytest.mark.asyncio
    async def test_upsert_adds_distinct_work_on_same_lesson(self):
        """Разные work_number на одной паре адресуются как multi-grade ячейка."""
        service = JournalGradeWriteService()
        lesson = Lesson(
            id=uuid4(),
            group_id=uuid4(),
            subject_id=uuid4(),
            date=date.today(),
            lesson_number=1,
            lesson_type=LessonType.LAB,
            work_number=1,
            is_cancelled=False,
        )
        existing = LessonGrade(
            id=uuid4(),
            lesson_id=lesson.id,
            student_id=uuid4(),
            work_number=1,
            grade=5,
            comment=None,
            created_by=uuid4(),
        )
        db = AsyncMock()
        service.list_cell_grades = AsyncMock(return_value=[existing])
        service._write_grade = AsyncMock(return_value=existing)

        await service.upsert_grade(
            db=db,
            lesson=lesson,
            student_id=existing.student_id,
            grade=4,
            work_number=2,
            comment=None,
            actor_id=uuid4(),
        )

        assert service._write_grade.await_args.kwargs["existing"] is None
        assert service._write_grade.await_args.kwargs["work_number"] == 2

    @pytest.mark.asyncio
    async def test_upsert_updates_matching_work_in_multi_grade_cell(self):
        service = JournalGradeWriteService()
        lesson = Lesson(
            id=uuid4(),
            group_id=uuid4(),
            subject_id=uuid4(),
            date=date.today(),
            lesson_number=1,
            lesson_type=LessonType.LAB,
            work_number=1,
            is_cancelled=False,
        )
        student_id = uuid4()
        first = LessonGrade(id=uuid4(), lesson_id=lesson.id, student_id=student_id, work_number=1, grade=5)
        second = LessonGrade(id=uuid4(), lesson_id=lesson.id, student_id=student_id, work_number=2, grade=4)
        db = AsyncMock()
        service.list_cell_grades = AsyncMock(return_value=[first, second])
        service._write_grade = AsyncMock(return_value=second)

        await service.upsert_grade(
            db=db,
            lesson=lesson,
            student_id=student_id,
            grade=5,
            work_number=2,
            comment=None,
            actor_id=uuid4(),
        )

        assert service._write_grade.await_args.kwargs["existing"] is second

    @pytest.mark.asyncio
    async def test_upsert_rejects_duplicate_work_number_conflict(self):
        service = JournalGradeWriteService()
        lesson = Lesson(
            id=uuid4(),
            group_id=uuid4(),
            subject_id=uuid4(),
            date=date.today(),
            lesson_number=1,
            lesson_type=LessonType.LAB,
            work_number=2,
            is_cancelled=False,
        )
        student_id = uuid4()
        grades = [
            LessonGrade(id=uuid4(), lesson_id=lesson.id, student_id=student_id, work_number=2, grade=4),
            LessonGrade(id=uuid4(), lesson_id=lesson.id, student_id=student_id, work_number=2, grade=5),
        ]
        db = AsyncMock()
        service.list_cell_grades = AsyncMock(return_value=grades)

        with pytest.raises(JournalGradeConflictError, match="Конфликт legacy-данных"):
            await service.upsert_grade(
                db=db,
                lesson=lesson,
                student_id=student_id,
                grade=5,
                work_number=2,
                comment=None,
                actor_id=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_replace_rejects_same_lesson_work_number_collision(self):
        service = JournalGradeWriteService()
        lesson = Lesson(id=uuid4(), group_id=uuid4(), subject_id=uuid4())
        student_id = uuid4()
        first = LessonGrade(id=uuid4(), lesson_id=lesson.id, student_id=student_id, work_number=1, grade=5)
        second = LessonGrade(id=uuid4(), lesson_id=lesson.id, student_id=student_id, work_number=2, grade=4)

        with pytest.raises(JournalGradeConflictError, match="уже есть оценка"):
            await service._replace_existing(
                AsyncMock(),
                lesson=lesson,
                existing=first,
                merge_target=second,
                grade=5,
                work_number=2,
                comment=None,
                actor_id=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_upsert_wraps_deadline_limit_as_validation_error(self, monkeypatch):
        service = JournalGradeWriteService()
        lesson = Lesson(
            id=uuid4(),
            group_id=uuid4(),
            subject_id=uuid4(),
            date=date.today(),
            lesson_number=1,
            lesson_type=LessonType.LAB,
            work_number=1,
            is_cancelled=False,
        )
        db = AsyncMock()
        student_id = uuid4()
        service.list_cell_grades = AsyncMock(return_value=[])
        monkeypatch.setattr(
            "app.services.journal_grade_service.validate_student_membership",
            AsyncMock(),
        )
        monkeypatch.setattr(
            "app.services.journal_grade_rules.get_max_allowed_grade",
            AsyncMock(return_value=4),
        )

        with pytest.raises(JournalGradeValidationError, match="Максимальная оценка"):
            await service.upsert_grade(
                db=db,
                lesson=lesson,
                student_id=student_id,
                grade=5,
                work_number=1,
                comment=None,
                actor_id=uuid4(),
            )


class TestLessonSheetService:
    """Тесты atomic lesson sheet flow."""

    @pytest.mark.asyncio
    async def test_save_sheet_preserves_metadata_when_field_omitted(self):
        service = LessonSheetService()
        lesson = Lesson(
            id=uuid4(),
            group_id=uuid4(),
            subject_id=uuid4(),
            date=date.today(),
            lesson_number=2,
            lesson_type=LessonType.LECTURE,
            topic="Старая тема",
            work_number=4,
            is_cancelled=False,
            ended_early=False,
        )
        db = AsyncMock()
        service._apply_attendance_updates = AsyncMock()
        service._apply_grade_updates = AsyncMock()
        service._build_response = AsyncMock(return_value={"lesson": lesson, "attendance": [], "grades": []})

        payload = LessonSheetSaveRequest(status="normal")

        await service.save_sheet(db, lesson, payload, actor_id=uuid4())

        assert lesson.topic == "Старая тема"
        assert lesson.work_number == 4

    @pytest.mark.asyncio
    async def test_save_grouped_sheet_saves_all_lessons_in_one_service_call(self):
        service = LessonSheetService()
        lesson_a = Lesson(
            id=uuid4(),
            group_id=uuid4(),
            subject_id=uuid4(),
            date=date.today(),
            lesson_number=1,
            lesson_type=LessonType.LECTURE,
            is_cancelled=False,
            ended_early=False,
        )
        lesson_b = Lesson(
            id=uuid4(),
            group_id=lesson_a.group_id,
            subject_id=lesson_a.subject_id,
            date=lesson_a.date,
            lesson_number=lesson_a.lesson_number,
            lesson_type=LessonType.LECTURE,
            is_cancelled=False,
            ended_early=False,
        )
        db = AsyncMock()
        service.save_sheet = AsyncMock(
            side_effect=[
                {"attendance": [{"student_id": uuid4(), "status": "PRESENT"}]},
                {"attendance": []},
            ]
        )
        payload = GroupedLectureSheetSaveRequest(
            status="normal",
            items=[
                GroupedLectureSheetSaveItem(lesson_id=lesson_a.id),
                GroupedLectureSheetSaveItem(lesson_id=lesson_b.id),
            ],
        )

        result = await service.save_grouped_sheet(
            db=db,
            lessons_by_id={lesson_a.id: lesson_a, lesson_b.id: lesson_b},
            payload=payload,
            actor_id=uuid4(),
        )

        assert service.save_sheet.await_count == 2
        assert [item["lesson_id"] for item in result["items"]] == [lesson_a.id, lesson_b.id]
