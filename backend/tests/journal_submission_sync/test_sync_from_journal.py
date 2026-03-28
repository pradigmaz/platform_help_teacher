"""Тесты синхронизации журнал → submission."""
import pytest
from uuid import uuid4
from datetime import datetime, timezone, date, timedelta
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Submission, SubmissionStatus, Lab, Lesson, User, Subject, Group
from app.models.schedule import LessonType
from app.models.user import UserRole
from app.models.group import GradingScale
from app.services.submission_journal_sync import journal_sync


def scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


@pytest.fixture
def sample_subject():
    """Тестовый предмет."""
    subject = Subject(
        id=uuid4(),
        name="Программирование",
        code="PROG",
        is_active=True,
    )
    subject.created_at = datetime.now(timezone.utc)
    subject.updated_at = datetime.now(timezone.utc)
    return subject


@pytest.fixture
def sample_group():
    """Тестовая группа."""
    group = Group(
        id=uuid4(),
        name="ИТ-11",
        code="IT11",
        invite_code="ABC12345",
        labs_count=10,
        grading_scale=GradingScale.TEN,
        default_max_grade=10,
        is_archived=False,
    )
    group.created_at = datetime.now(timezone.utc)
    group.updated_at = datetime.now(timezone.utc)
    return group


@pytest.fixture
def sample_student(sample_group):
    """Тестовый студент."""
    return User(
        id=uuid4(),
        full_name="Иванов Иван Иванович",
        username="ivanov",
        role=UserRole.STUDENT,
        group_id=sample_group.id,
        subgroup=1,
        is_active=True,
    )


@pytest.fixture
def sample_teacher():
    """Тестовый преподаватель."""
    return User(
        id=uuid4(),
        full_name="Петров Пётр Петрович",
        username="petrov",
        role=UserRole.TEACHER,
        is_active=True,
    )


@pytest.fixture
def sample_lab(sample_subject):
    """Тестовая опубликованная лаба."""
    lab = Lab(
        id=uuid4(),
        number=1,
        subject_id=sample_subject.id,
        title="Лабораторная работа №1",
        topic="Введение",
        goal="Изучить основы",
        theory_content={"root": {"children": []}},
        practice_content={"root": {"children": []}},
        variants=[{"number": 1, "description": "Вариант 1"}],
        questions=["Вопрос 1?", "Вопрос 2?"],
        max_grade=5,
        is_sequential=True,
        is_published=True,
        deleted_at=None,
    )
    lab.created_at = datetime.now(timezone.utc)
    lab.updated_at = datetime.now(timezone.utc)
    return lab


@pytest.fixture
def sample_lesson(sample_group, sample_subject):
    """Тестовое занятие (LAB)."""
    lesson = Lesson(
        id=uuid4(),
        group_id=sample_group.id,
        subject_id=sample_subject.id,
        date=date.today(),
        lesson_number=1,
        lesson_type=LessonType.LAB,
        topic="Лабораторная работа №1",
        work_number=1,
        is_cancelled=False,
    )
    lesson.created_at = datetime.now(timezone.utc)
    lesson.updated_at = datetime.now(timezone.utc)
    return lesson


class TestSyncFromJournal:
    """Тесты метода sync_from_journal."""

    @pytest.mark.asyncio
    async def test_create_submission_from_journal_grade(
        self,
        mock_db: AsyncMock,
        sample_student: User,
        sample_lab: Lab,
        sample_lesson: Lesson,
        sample_teacher: User,
    ):
        """
        Subtask 6.1: Тест создания Submission при выставлении оценки за лабу.
        
        Сценарий:
        - Создать lesson (LAB), lab (published), student
        - Вызвать journal_sync.sync_from_journal()
        - Проверить: submission создан с is_manual=True, status=ACCEPTED, grade=оценка
        """
        # Arrange
        grade = 5
        comment = "Отлично выполнено"
        
        # Mock: find_published_lab возвращает лабу
        async def mock_find_published_lab(db, subject_id, work_number):
            if subject_id == sample_lesson.subject_id and work_number == 1:
                return sample_lab
            return None
        
        # Mock: SELECT Submission возвращает None (не существует)
        mock_db.execute.return_value = scalar_result(None)
        
        # Подменяем метод
        original_find = journal_sync.find_published_lab
        journal_sync.find_published_lab = mock_find_published_lab
        
        try:
            # Act
            submission = await journal_sync.sync_from_journal(
                mock_db,
                sample_student.id,
                sample_lesson,
                work_number=1,
                grade=grade,
                comment=comment,
                created_by=sample_teacher.id,
            )
            
            # Assert
            assert submission is not None
            assert submission.user_id == sample_student.id
            assert submission.lab_id == sample_lab.id
            assert submission.is_manual is True
            assert submission.status == SubmissionStatus.ACCEPTED
            assert submission.grade == grade
            assert submission.feedback == comment
            assert submission.accepted_at is not None
            assert submission.lesson_id == sample_lesson.id
            assert submission.lesson_date == sample_lesson.date
            assert submission.lesson_number == sample_lesson.lesson_number
            
            # Проверяем историю
            assert len(submission.history) == 1
            assert submission.history[0]["action"] == "created_from_journal"
            assert submission.history[0]["grade"] == grade
            assert submission.history[0]["comment"] == comment
            assert submission.history[0]["by"] == str(sample_teacher.id)
            
            # Проверяем что submission добавлен в БД
            mock_db.add.assert_called_once()
            mock_db.flush.assert_called_once()
        finally:
            # Восстанавливаем оригинальный метод
            journal_sync.find_published_lab = original_find

    @pytest.mark.asyncio
    async def test_update_existing_submission_grade(
        self,
        mock_db: AsyncMock,
        sample_student: User,
        sample_lab: Lab,
        sample_lesson: Lesson,
        sample_teacher: User,
    ):
        """
        Subtask 6.2: Тест обновления grade существующего Submission.
        
        Сценарий:
        - Создать submission со статусом READY
        - Вызвать journal_sync.sync_from_journal() с новой оценкой
        - Проверить: submission.grade обновлён, status=ACCEPTED
        """
        # Arrange
        existing_submission = Submission(
            id=uuid4(),
            user_id=sample_student.id,
            lab_id=sample_lab.id,
            status=SubmissionStatus.READY,
            is_manual=False,
            grade=None,
            feedback=None,
            history=[{
                "action": "ready",
                "at": datetime.now(timezone.utc).isoformat(),
            }],
        )
        existing_submission.created_at = datetime.now(timezone.utc)
        existing_submission.updated_at = datetime.now(timezone.utc)
        
        new_grade = 4
        new_comment = "Хорошо"
        
        # Mock: find_published_lab возвращает лабу
        async def mock_find_published_lab(db, subject_id, work_number):
            return sample_lab
        
        # Mock: SELECT Submission возвращает существующий submission
        mock_db.execute.return_value = scalar_result(existing_submission)
        
        original_find = journal_sync.find_published_lab
        journal_sync.find_published_lab = mock_find_published_lab
        
        try:
            # Act
            submission = await journal_sync.sync_from_journal(
                mock_db,
                sample_student.id,
                sample_lesson,
                work_number=1,
                grade=new_grade,
                comment=new_comment,
                created_by=sample_teacher.id,
            )
            
            # Assert
            assert submission is not None
            assert submission.id == existing_submission.id
            assert submission.grade == new_grade
            assert submission.status == SubmissionStatus.ACCEPTED
            assert submission.feedback == new_comment
            assert submission.accepted_at is not None
            assert submission.lesson_id == sample_lesson.id
            assert submission.lesson_date == sample_lesson.date
            assert submission.lesson_number == sample_lesson.lesson_number
            
            # Проверяем что история обновлена
            assert len(submission.history) == 2
            assert submission.history[1]["action"] == "graded_from_journal"
            assert submission.history[1]["grade"] == new_grade
            
            # Проверяем что add НЕ вызван (обновление, не создание)
            mock_db.add.assert_not_called()
        finally:
            journal_sync.find_published_lab = original_find

    @pytest.mark.asyncio
    async def test_no_submission_for_nonexistent_lab(
        self,
        mock_db: AsyncMock,
        sample_student: User,
        sample_lesson: Lesson,
        sample_teacher: User,
    ):
        """
        Subtask 6.3: Тест что Submission не создаётся для несуществующей лабы.
        
        Сценарий:
        - Создать lesson без лабы (work_number не существует)
        - Вызвать journal_sync.sync_from_journal()
        - Проверить: return None, submission не создан
        """
        # Arrange
        nonexistent_work_number = 999
        
        # Mock: find_published_lab возвращает None
        async def mock_find_published_lab(db, subject_id, work_number):
            return None
        
        original_find = journal_sync.find_published_lab
        journal_sync.find_published_lab = mock_find_published_lab
        
        try:
            # Act
            submission = await journal_sync.sync_from_journal(
                mock_db,
                sample_student.id,
                sample_lesson,
                work_number=nonexistent_work_number,
                grade=5,
                comment="Test",
                created_by=sample_teacher.id,
            )
            
            # Assert
            assert submission is None
            mock_db.add.assert_not_called()
        finally:
            journal_sync.find_published_lab = original_find

    @pytest.mark.asyncio
    async def test_no_submission_for_lesson_without_subject(
        self,
        mock_db: AsyncMock,
        sample_student: User,
        sample_group: Group,
        sample_teacher: User,
    ):
        """
        Subtask 6.4: Тест что Submission не создаётся для занятия без subject_id.
        
        Сценарий:
        - Создать lesson без subject_id
        - Вызвать journal_sync.sync_from_journal()
        - Проверить: return None
        """
        # Arrange
        lesson_without_subject = Lesson(
            id=uuid4(),
            group_id=sample_group.id,
            subject_id=None,  # Нет предмета
            date=date.today(),
            lesson_number=1,
            lesson_type=LessonType.LAB,
            work_number=1,
            is_cancelled=False,
        )
        
        # Act
        submission = await journal_sync.sync_from_journal(
            mock_db,
            sample_student.id,
            lesson_without_subject,
            work_number=1,
            grade=5,
            comment="Test",
            created_by=sample_teacher.id,
        )
        
        # Assert
        assert submission is None
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_bulk_grade_creates_multiple_submissions(
        self,
        mock_db: AsyncMock,
        sample_group: Group,
        sample_subject: Subject,
        sample_lab: Lab,
        sample_lesson: Lesson,
        sample_teacher: User,
    ):
        """
        Subtask 6.5: Тест bulk выставления оценок → создаются несколько Submissions.
        
        Сценарий:
        - Создать 3 студента, 1 лабу
        - Вызвать journal_sync.sync_from_journal() для каждого студента
        - Проверить: 3 submissions созданы
        """
        # Arrange
        students = [
            User(
                id=uuid4(),
                full_name=f"Студент {i}",
                username=f"student{i}",
                role=UserRole.STUDENT,
                group_id=sample_group.id,
                subgroup=1,
                is_active=True,
            )
            for i in range(1, 4)
        ]
        
        grades = [5, 4, 3]
        submissions_created = []
        
        # Mock: find_published_lab возвращает лабу
        async def mock_find_published_lab(db, subject_id, work_number):
            return sample_lab
        
        # Mock: SELECT Submission возвращает None для каждого студента
        def mock_execute_side_effect(*args, **kwargs):
            return scalar_result(None)
        
        mock_db.execute.side_effect = mock_execute_side_effect
        
        original_find = journal_sync.find_published_lab
        journal_sync.find_published_lab = mock_find_published_lab
        
        try:
            # Act
            for student, grade in zip(students, grades):
                submission = await journal_sync.sync_from_journal(
                    mock_db,
                    student.id,
                    sample_lesson,
                    work_number=1,
                    grade=grade,
                    comment=f"Оценка {grade}",
                    created_by=sample_teacher.id,
                )
                submissions_created.append(submission)
            
            # Assert
            assert len(submissions_created) == 3
            assert all(s is not None for s in submissions_created)
            assert all(s.status == SubmissionStatus.ACCEPTED for s in submissions_created)
            assert [s.grade for s in submissions_created] == grades
            
            # Проверяем что add вызван 3 раза
            assert mock_db.add.call_count == 3
        finally:
            journal_sync.find_published_lab = original_find

    @pytest.mark.asyncio
    async def test_race_condition_handled_correctly(
        self,
        mock_db: AsyncMock,
        sample_student: User,
        sample_lab: Lab,
        sample_lesson: Lesson,
        sample_teacher: User,
    ):
        """
        Subtask 6.6: Тест обработки race condition → IntegrityError.
        
        Сценарий:
        - Создать submission вручную между SELECT и INSERT
        - Проверить: IntegrityError пойман, submission обновлён
        """
        from sqlalchemy.exc import IntegrityError
        
        # Arrange
        grade = 5
        comment = "Test"
        
        # Submission который будет "создан" другим запросом
        concurrent_submission = Submission(
            id=uuid4(),
            user_id=sample_student.id,
            lab_id=sample_lab.id,
            status=SubmissionStatus.NEW,
            is_manual=False,
            grade=None,
            feedback=None,
            history=[],
        )
        concurrent_submission.created_at = datetime.now(timezone.utc)
        concurrent_submission.updated_at = datetime.now(timezone.utc)
        
        # Mock: find_published_lab возвращает лабу
        async def mock_find_published_lab(db, subject_id, work_number):
            return sample_lab
        
        # Mock: первый SELECT возвращает None, второй (после IntegrityError) — submission
        call_count = 0
        
        def mock_execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Первый вызов: submission не найден
                return scalar_result(None)
            # Второй вызов (после IntegrityError): submission найден
            return scalar_result(concurrent_submission)
        
        mock_db.execute.side_effect = mock_execute_side_effect
        
        # Mock: flush вызывает IntegrityError при первой попытке
        flush_call_count = 0
        
        async def mock_flush_side_effect():
            nonlocal flush_call_count
            flush_call_count += 1
            if flush_call_count == 1:
                raise IntegrityError("duplicate key", None, None)
        
        mock_db.flush.side_effect = mock_flush_side_effect
        
        original_find = journal_sync.find_published_lab
        journal_sync.find_published_lab = mock_find_published_lab
        
        try:
            # Act
            submission = await journal_sync.sync_from_journal(
                mock_db,
                sample_student.id,
                sample_lesson,
                work_number=1,
                grade=grade,
                comment=comment,
                created_by=sample_teacher.id,
            )
            
            # Assert
            assert submission is not None
            assert submission.id == concurrent_submission.id
            assert submission.grade == grade
            assert submission.status == SubmissionStatus.ACCEPTED
            assert submission.feedback == comment
            
            # Outer transaction не откатывается: race condition локализуется nested savepoint.
            mock_db.rollback.assert_not_called()
            
            # Проверяем что история обновлена
            assert len(submission.history) == 1
            assert submission.history[0]["action"] == "graded_from_journal"
        finally:
            journal_sync.find_published_lab = original_find


class TestFindPublishedLab:
    """Тесты метода find_published_lab."""

    @pytest.mark.asyncio
    async def test_find_published_lab_success(
        self,
        mock_db: AsyncMock,
        sample_subject: Subject,
        sample_lab: Lab,
    ):
        """Тест успешного поиска опубликованной лабы."""
        # Arrange
        mock_db.execute.return_value = scalar_result(sample_lab)
        
        # Act
        lab = await journal_sync.find_published_lab(
            mock_db,
            sample_subject.id,
            work_number=1,
        )
        
        # Assert
        assert lab is not None
        assert lab.id == sample_lab.id
        assert lab.number == 1
        assert lab.is_published is True

    @pytest.mark.asyncio
    async def test_find_published_lab_not_found(
        self,
        mock_db: AsyncMock,
        sample_subject: Subject,
    ):
        """Тест что метод возвращает None если лаба не найдена."""
        # Arrange
        mock_db.execute.return_value = scalar_result(None)
        
        # Act
        lab = await journal_sync.find_published_lab(
            mock_db,
            sample_subject.id,
            work_number=999,
        )
        
        # Assert
        assert lab is None


class TestRollbackFromJournal:
    """Тесты rollback submission-проекции."""

    @pytest.mark.asyncio
    async def test_rollback_updates_submission_for_unpublished_lab(
        self,
        mock_db: AsyncMock,
        sample_student: User,
        sample_lab: Lab,
        sample_lesson: Lesson,
        sample_teacher: User,
    ):
        """Rollback не должен зависеть от is_published/deleted_at у лабы."""
        sample_lab.is_published = False
        sample_lab.deleted_at = datetime.now(timezone.utc)
        submission = Submission(
            id=uuid4(),
            user_id=sample_student.id,
            lab_id=sample_lab.id,
            status=SubmissionStatus.ACCEPTED,
            is_manual=True,
            grade=5,
            feedback="OK",
            history=[],
        )
        submission.created_at = datetime.now(timezone.utc)
        submission.updated_at = datetime.now(timezone.utc)
        mock_db.execute.return_value = scalar_result(submission)

        rolled_back = await journal_sync.rollback_from_journal(
            mock_db,
            student_id=sample_student.id,
            lesson=sample_lesson,
            work_number=sample_lab.number,
            created_by=sample_teacher.id,
        )

        assert rolled_back is True
        assert submission.status == SubmissionStatus.NEW
        assert submission.grade is None
        assert submission.feedback is None
        assert submission.accepted_at is None
        assert submission.lesson_id is None
        assert submission.lesson_date is None
        assert submission.lesson_number is None
        assert submission.history[-1]["action"] == "grade_removed_from_journal"

    @pytest.mark.asyncio
    async def test_find_published_lab_ignores_deleted(
        self,
        mock_db: AsyncMock,
        sample_subject: Subject,
    ):
        """Тест что метод игнорирует удалённые лабы."""
        # Arrange
        deleted_lab = Lab(
            id=uuid4(),
            number=1,
            subject_id=sample_subject.id,
            title="Удалённая лаба",
            is_published=True,
            deleted_at=datetime.now(timezone.utc),  # Удалена
        )
        
        mock_db.execute.return_value = scalar_result(None)  # Не найдена
        
        # Act
        lab = await journal_sync.find_published_lab(
            mock_db,
            sample_subject.id,
            work_number=1,
        )
        
        # Assert
        assert lab is None

    @pytest.mark.asyncio
    async def test_find_published_lab_ignores_unpublished(
        self,
        mock_db: AsyncMock,
        sample_subject: Subject,
    ):
        """Тест что метод игнорирует неопубликованные лабы."""
        # Arrange
        unpublished_lab = Lab(
            id=uuid4(),
            number=1,
            subject_id=sample_subject.id,
            title="Неопубликованная лаба",
            is_published=False,  # Не опубликована
            deleted_at=None,
        )
        
        mock_db.execute.return_value = scalar_result(None)  # Не найдена
        
        # Act
        lab = await journal_sync.find_published_lab(
            mock_db,
            sample_subject.id,
            work_number=1,
        )
        
        # Assert
        assert lab is None
