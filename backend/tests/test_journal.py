"""
Тесты для модуля Journal (оценки и посещаемость).
"""
import pytest
from uuid import uuid4
from datetime import date

from pydantic import ValidationError

from app.models import LessonGrade, Attendance, AttendanceStatus, Lesson, User, Group
from app.models.user import UserRole
from app.models.schedule import LessonType
from app.schemas.lesson_grade import (
    LessonGradeCreate, LessonGradeUpdate, GradeItem, 
    BulkGradeCreate, BulkAttendanceUpdate, AttendanceRecord
)


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
            ]
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
            ]
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
                ]
            )


class TestAttendanceStatusEnum:
    """Тесты enum статусов посещаемости."""
    
    def test_valid_statuses(self):
        """Все валидные статусы существуют."""
        valid = ['PRESENT', 'ABSENT', 'LATE', 'EXCUSED']
        for status in valid:
            assert hasattr(AttendanceStatus, status)
    
    def test_status_values(self):
        """Значения enum корректны."""
        assert AttendanceStatus.PRESENT.value == 'PRESENT'
        assert AttendanceStatus.ABSENT.value == 'ABSENT'
        assert AttendanceStatus.LATE.value == 'LATE'
        assert AttendanceStatus.EXCUSED.value == 'EXCUSED'


class TestLessonGradeModel:
    """Тесты модели LessonGrade."""
    
    def test_model_has_check_constraint(self):
        """Модель имеет CheckConstraint на grade."""
        constraints = [c.name for c in LessonGrade.__table__.constraints 
                      if hasattr(c, 'name') and c.name]
        assert 'ck_lesson_grade_range' in constraints
    
    def test_model_has_work_number_index(self):
        """Модель имеет индекс на work_number."""
        indexes = [idx.name for idx in LessonGrade.__table__.indexes]
        assert 'idx_lesson_grades_work_number' in indexes
    
    def test_model_has_lesson_student_index(self):
        """Модель имеет составной индекс lesson_id + student_id."""
        indexes = [idx.name for idx in LessonGrade.__table__.indexes]
        assert 'idx_lesson_grades_lesson_student' in indexes


class TestLessonGradeCreate:
    """Тесты схемы создания оценки."""
    
    def test_create_schema_valid(self):
        """Валидная схема создания."""
        data = LessonGradeCreate(
            lesson_id=uuid4(),
            student_id=uuid4(),
            grade=5,
            work_number=1,
            comment="Отлично"
        )
        assert data.grade == 5
        assert data.work_number == 1
    
    def test_create_schema_minimal(self):
        """Минимальная схема (только обязательные поля)."""
        data = LessonGradeCreate(
            lesson_id=uuid4(),
            student_id=uuid4(),
            grade=3
        )
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
