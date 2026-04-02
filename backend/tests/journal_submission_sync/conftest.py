"""Shared fixtures for journal -> submission projection tests."""

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from app.models import Group, Lab, Lesson, Subject, Submission, User
from app.models.group import GradingScale
from app.models.schedule import LessonType
from app.models.user import UserRole


def scalar_result(value):
    """Build a result object exposing scalar_one_or_none()."""
    from unittest.mock import MagicMock

    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


@pytest.fixture
def sample_subject() -> Subject:
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
def sample_group() -> Group:
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
def sample_student(sample_group: Group) -> User:
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
def sample_teacher() -> User:
    return User(
        id=uuid4(),
        full_name="Петров Пётр Петрович",
        username="petrov",
        role=UserRole.TEACHER,
        is_active=True,
    )


@pytest.fixture
def sample_lab(sample_subject: Subject) -> Lab:
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
def sample_lesson(sample_group: Group, sample_subject: Subject) -> Lesson:
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


def make_submission(*, user_id, lab_id, status, is_manual=False, grade=None, feedback=None, history=None) -> Submission:
    submission = Submission(
        id=uuid4(),
        user_id=user_id,
        lab_id=lab_id,
        status=status,
        is_manual=is_manual,
        grade=grade,
        feedback=feedback,
        history=history or [],
    )
    submission.created_at = datetime.now(timezone.utc)
    submission.updated_at = datetime.now(timezone.utc)
    return submission
