"""Pytest fixtures for testing."""
# Monkeypatch SQLAlchemy for Python 3.14+ compatibility
import sys
if sys.version_info >= (3, 14):
    import typing
    import sqlalchemy.util.typing
    sqlalchemy.util.typing.make_union_type = lambda *types: typing.Union.__class_getitem__(types)


import pytest
import pytest_asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.models.group import GradingScale
from app.models.user import UserRole


@pytest_asyncio.fixture
async def mock_db() -> AsyncGenerator[AsyncMock, None]:
    """Mock database session."""
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    yield db


@pytest.fixture
def sample_group() -> models.Group:
    """Sample group for testing."""
    from uuid import uuid4
    from datetime import UTC, datetime
    
    group = models.Group(
        id=uuid4(),
        name="ИТ-11",
        code="IT11",
        invite_code="ABC12345",
        labs_count=10,
        grading_scale=GradingScale.TEN,
        default_max_grade=10,
        is_archived=False,
    )
    group.created_at = datetime.now(UTC)
    return group


@pytest.fixture
def sample_student() -> models.User:
    """Sample student for testing."""
    from uuid import uuid4
    
    return models.User(
        id=uuid4(),
        full_name="Иванов Иван Иванович",
        username="ivanov",
        role=UserRole.STUDENT,
        invite_code="STU12345",
        subgroup=1,
        is_active=True,
    )


@pytest.fixture
def sample_group_create() -> schemas.GroupCreate:
    """Sample group create schema."""
    return schemas.GroupCreate(
        name="ИТ-21",
        code="IT21",
        students=[
            schemas.StudentImport(full_name="Петров Пётр Петрович"),
            schemas.StudentImport(full_name="Сидоров Сидор Сидорович"),
        ],
        labs_count=8,
        grading_scale=GradingScale.TEN,
        default_max_grade=10,
    )
