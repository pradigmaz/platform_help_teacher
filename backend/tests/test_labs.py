"""Тесты для модуля labs."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

# Импортируем напрямую, минуя __init__.py
import sys
sys.path.insert(0, '/app')

from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.submission import Submission, SubmissionStatus
from app.models.schedule import LessonType
from app.schemas.lab import LabCreate, LabUpdate
from app.core.constants import (
    LAB_CONTENT_MAX_SIZE_BYTES,
    LAB_MAX_VARIANTS,
    LAB_MAX_QUESTIONS,
)


@pytest.fixture
def sample_lab() -> Lab:
    """Sample lab for testing."""
    lab = Lab(
        id=uuid4(),
        number=1,
        title="Лабораторная работа №1",
        topic="Введение",
        goal="Изучить основы",
        theory_content={"root": {"children": []}},
        practice_content={"root": {"children": []}},
        variants=[{"number": 1, "description": "Вариант 1"}],
        questions=["Вопрос 1?", "Вопрос 2?"],
        max_grade=5,
        is_sequential=True,
        is_published=False,
        public_code=None,
        deleted_at=None,
    )
    lab.created_at = datetime.now(timezone.utc)
    lab.updated_at = datetime.now(timezone.utc)
    return lab


@pytest.fixture
def sample_submission(sample_lab: Lab) -> Submission:
    """Sample submission for testing."""
    sub = Submission(
        id=uuid4(),
        user_id=uuid4(),
        lab_id=sample_lab.id,
        status=SubmissionStatus.READY,
        variant_number=1,
        grade=None,
        feedback=None,
        history=[],
        ready_at=datetime.now(timezone.utc),
    )
    sub.created_at = datetime.now(timezone.utc)
    sub.updated_at = datetime.now(timezone.utc)
    return sub


class TestLabCreateValidation:
    """Тесты валидации создания лабораторной работы."""

    def test_valid_lab_create(self):
        """Тест создания валидной лабы."""
        lab = LabCreate(
            number=1,
            title="Тестовая лаба",
            max_grade=10,
        )
        assert lab.number == 1
        assert lab.title == "Тестовая лаба"
        assert lab.max_grade == 10

    def test_number_must_be_positive(self):
        """Тест что номер лабы должен быть положительным."""
        with pytest.raises(ValueError):
            LabCreate(number=0, title="Test")
        
        with pytest.raises(ValueError):
            LabCreate(number=-1, title="Test")

    def test_max_grade_range(self):
        """Тест диапазона max_grade (1-100)."""
        # Валидные значения
        lab1 = LabCreate(title="Test", max_grade=1)
        assert lab1.max_grade == 1
        
        lab100 = LabCreate(title="Test", max_grade=100)
        assert lab100.max_grade == 100
        
        # Невалидные значения
        with pytest.raises(ValueError):
            LabCreate(title="Test", max_grade=0)
        
        with pytest.raises(ValueError):
            LabCreate(title="Test", max_grade=101)

    def test_title_length_limit(self):
        """Тест ограничения длины заголовка."""
        # Валидный заголовок
        lab = LabCreate(title="A" * 200)
        assert len(lab.title) == 200
        
        # Слишком длинный заголовок
        with pytest.raises(ValueError):
            LabCreate(title="A" * 201)

    def test_content_size_limit(self):
        """Тест ограничения размера контента."""
        # Создаём контент больше лимита
        large_content = {"data": "x" * (LAB_CONTENT_MAX_SIZE_BYTES + 1000)}
        
        with pytest.raises(ValueError, match="Content too large"):
            LabCreate(title="Test", theory_content=large_content)

    def test_variants_count_limit(self):
        """Тест ограничения количества вариантов."""
        too_many_variants = [{"number": i} for i in range(LAB_MAX_VARIANTS + 1)]
        
        with pytest.raises(ValueError, match="Too many variants"):
            LabCreate(title="Test", variants=too_many_variants)

    def test_questions_count_limit(self):
        """Тест ограничения количества вопросов."""
        too_many_questions = [f"Вопрос {i}?" for i in range(LAB_MAX_QUESTIONS + 1)]
        
        with pytest.raises(ValueError, match="Too many questions"):
            LabCreate(title="Test", questions=too_many_questions)


class TestLabService:
    """Тесты бизнес-логики лабораторных работ."""

    @pytest.mark.asyncio
    async def test_create_lab(self, mock_db: AsyncMock):
        """Тест создания лабы."""
        from app.services.lab_service import LabService
        service = LabService()
        lab_in = LabCreate(title="Новая лаба", number=1)
        
        result = await service.create(mock_db, lab_in)
        
        assert result.title == "Новая лаба"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_lab(self, mock_db: AsyncMock, sample_lab: Lab):
        """Тест публикации лабы."""
        from app.services.lab_service import LabService
        service = LabService()
        
        # Mock get_by_public_code возвращает None (код уникален)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        code = await service.publish(mock_db, sample_lab)
        
        assert len(code) == 8
        assert sample_lab.is_published is True
        assert sample_lab.public_code == code
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_publish_returns_existing_code(self, mock_db: AsyncMock, sample_lab: Lab):
        """Тест что повторная публикация возвращает существующий код."""
        from app.services.lab_service import LabService
        service = LabService()
        sample_lab.public_code = "abc12345"
        
        code = await service.publish(mock_db, sample_lab)
        
        assert code == "abc12345"
        assert sample_lab.is_published is True

    @pytest.mark.asyncio
    async def test_unpublish_lab(self, mock_db: AsyncMock, sample_lab: Lab):
        """Тест снятия лабы с публикации."""
        from app.services.lab_service import LabService
        service = LabService()
        sample_lab.is_published = True
        sample_lab.public_code = "abc12345"
        
        await service.unpublish(mock_db, sample_lab)
        
        assert sample_lab.is_published is False
        assert sample_lab.public_code is None
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_soft_delete_lab(self, mock_db: AsyncMock, sample_lab: Lab):
        """Тест мягкого удаления лабы."""
        from app.services.lab_service import LabService
        service = LabService()
        sample_lab.is_published = True
        sample_lab.public_code = "abc12345"
        
        await service.soft_delete(mock_db, sample_lab)
        
        assert sample_lab.deleted_at is not None
        assert sample_lab.is_published is False
        assert sample_lab.public_code is None
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_restore_lab(self, mock_db: AsyncMock, sample_lab: Lab):
        """Тест восстановления удалённой лабы."""
        from app.services.lab_service import LabService
        service = LabService()
        sample_lab.deleted_at = datetime.now(timezone.utc)
        
        await service.restore(mock_db, sample_lab)
        
        assert sample_lab.deleted_at is None
        mock_db.commit.assert_called()

    def test_generate_public_code_length(self):
        """Тест длины генерируемого кода."""
        from app.services.lab_service import LabService
        service = LabService()
        code = service.generate_public_code()
        
        assert len(code) == 8

    def test_generate_public_code_uniqueness(self):
        """Тест уникальности генерируемых кодов."""
        from app.services.lab_service import LabService
        service = LabService()
        codes = {service.generate_public_code() for _ in range(100)}
        
        # Все 100 кодов должны быть уникальными
        assert len(codes) == 100


class TestSubmissionService:
    """Тесты бизнес-логики сдачи работ."""

    @pytest.mark.asyncio
    async def test_accept_submission(self, mock_db: AsyncMock, sample_submission: Submission):
        """Тест приёма работы."""
        from app.services.submission_service import SubmissionService
        service = SubmissionService()
        sample_submission.lab = MagicMock()
        sample_submission.lab.lesson_id = None
        sample_submission.lab.subject_id = None
        
        result = await service.accept(
            mock_db, sample_submission, grade=5, comment="Отлично", accepted_by=uuid4()
        )
        
        assert result["status"] == "accepted"
        assert result["grade"] == 5
        assert sample_submission.status == SubmissionStatus.ACCEPTED
        assert sample_submission.grade == 5
        assert sample_submission.accepted_at is not None
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_accept_submission_wrong_status(self, mock_db: AsyncMock, sample_submission: Submission):
        """Тест что нельзя принять работу с неправильным статусом."""
        from app.services.submission_service import SubmissionService
        service = SubmissionService()
        sample_submission.status = SubmissionStatus.NEW
        
        with pytest.raises(ValueError, match="Cannot accept"):
            await service.accept(mock_db, sample_submission, grade=5, comment=None, accepted_by=uuid4())

    @pytest.mark.asyncio
    async def test_reject_submission(self, mock_db: AsyncMock, sample_submission: Submission):
        """Тест отклонения работы."""
        from app.services.submission_service import SubmissionService
        service = SubmissionService()
        
        result = await service.reject(
            mock_db, sample_submission, comment="Доработать", rejected_by=uuid4()
        )
        
        assert result["status"] == "rejected"
        assert sample_submission.status == SubmissionStatus.REJECTED
        assert sample_submission.feedback == "Доработать"
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_reject_submission_wrong_status(self, mock_db: AsyncMock, sample_submission: Submission):
        """Тест что нельзя отклонить работу с неправильным статусом."""
        from app.services.submission_service import SubmissionService
        service = SubmissionService()
        sample_submission.status = SubmissionStatus.ACCEPTED
        
        with pytest.raises(ValueError, match="Cannot reject"):
            await service.reject(mock_db, sample_submission, comment="Test", rejected_by=uuid4())

    @pytest.mark.asyncio
    async def test_accept_adds_history(self, mock_db: AsyncMock, sample_submission: Submission):
        """Тест что приём добавляет запись в историю."""
        from app.services.submission_service import SubmissionService
        service = SubmissionService()
        sample_submission.lab = MagicMock()
        sample_submission.lab.lesson_id = None
        sample_submission.lab.subject_id = None
        initial_history_len = len(sample_submission.history)
        
        await service.accept(mock_db, sample_submission, grade=4, comment="Хорошо", accepted_by=uuid4())
        
        assert len(sample_submission.history) == initial_history_len + 1
        assert sample_submission.history[-1]["action"] == "accepted"
        assert sample_submission.history[-1]["grade"] == 4


class TestGradeRangeValidation:
    """Тесты валидации диапазона оценок."""

    def test_grade_range_2_to_5(self):
        """Тест что оценка должна быть в диапазоне 2-5."""
        from pydantic import ValidationError
        from app.api.v1.endpoints.admin_lab_queue import AcceptSubmissionRequest
        
        # Валидные значения
        req2 = AcceptSubmissionRequest(grade=2)
        assert req2.grade == 2
        
        req5 = AcceptSubmissionRequest(grade=5)
        assert req5.grade == 5
        
        # Невалидные значения
        with pytest.raises(ValidationError):
            AcceptSubmissionRequest(grade=1)
        
        with pytest.raises(ValidationError):
            AcceptSubmissionRequest(grade=6)


class TestStudentLabService:
    """Тесты sync-ready контекста пары."""

    @pytest.mark.asyncio
    async def test_mark_ready_stores_lesson_context(self, mock_db: AsyncMock):
        from app.services.student_lab_service import StudentLabService

        service = StudentLabService()
        user_id = uuid4()
        lab_id = uuid4()
        lesson = Lesson(
            id=uuid4(),
            group_id=uuid4(),
            subject_id=uuid4(),
            date=datetime.now(timezone.utc).date(),
            lesson_number=3,
            lesson_type=LessonType.LAB,
        )
        mock_db.refresh = AsyncMock()
        service.get_user_submission_for_lab = AsyncMock(return_value=None)

        submission = await service.mark_ready(mock_db, user_id, lab_id, variant_number=2, lesson=lesson)

        assert submission.lesson_id == lesson.id
        assert submission.lesson_date == lesson.date
        assert submission.lesson_number == lesson.lesson_number
        mock_db.commit.assert_awaited_once()
