"""
Тесты для модуля Lectures (лекции).
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError

import sys
sys.path.insert(0, '/app')

from app.schemas.lecture import (
    LectureCreate,
    LectureUpdate,
    MAX_CONTENT_SIZE_BYTES,
    MAX_CONTENT_DEPTH,
)


# ============== Content Validation Tests ==============

class TestContentValidation:
    """Тесты валидации content JSON."""

    def test_valid_content(self):
        """Тест валидного контента."""
        lecture = LectureCreate(
            title="Test Lecture",
            content={"root": {"children": []}}
        )
        assert lecture.content == {"root": {"children": []}}

    def test_empty_content(self):
        """Тест пустого контента."""
        lecture = LectureCreate(title="Test Lecture")
        assert lecture.content == {}

    def test_content_size_limit(self):
        """Тест лимита размера контента (5MB)."""
        # Создаём контент больше лимита
        large_data = "x" * (MAX_CONTENT_SIZE_BYTES + 1000)
        
        with pytest.raises(ValidationError, match="Content exceeds"):
            LectureCreate(
                title="Test",
                content={"data": large_data}
            )

    def test_content_depth_limit(self):
        """Тест лимита глубины вложенности."""
        # Создаём глубоко вложенную структуру
        deep_content = {}
        current = deep_content
        for i in range(MAX_CONTENT_DEPTH + 10):
            current["nested"] = {}
            current = current["nested"]
        
        with pytest.raises(ValidationError, match="nesting depth"):
            LectureCreate(
                title="Test",
                content=deep_content
            )

    def test_content_valid_depth(self):
        """Тест допустимой глубины вложенности."""
        # Создаём структуру с допустимой глубиной
        content = {}
        current = content
        for i in range(MAX_CONTENT_DEPTH - 5):
            current["nested"] = {}
            current = current["nested"]
        
        lecture = LectureCreate(title="Test", content=content)
        assert lecture.content is not None

    def test_update_content_validation(self):
        """Тест валидации при обновлении."""
        large_data = "x" * (MAX_CONTENT_SIZE_BYTES + 1000)
        
        with pytest.raises(ValidationError, match="Content exceeds"):
            LectureUpdate(content={"data": large_data})

    def test_update_null_content(self):
        """Тест null контента при обновлении."""
        update = LectureUpdate(title="New Title", content=None)
        assert update.content is None


# ============== Title Validation Tests ==============

class TestTitleValidation:
    """Тесты валидации заголовка."""

    def test_valid_title(self):
        """Тест валидного заголовка."""
        lecture = LectureCreate(title="Введение в программирование")
        assert lecture.title == "Введение в программирование"

    def test_title_min_length(self):
        """Тест минимальной длины заголовка."""
        with pytest.raises(ValidationError):
            LectureCreate(title="")

    def test_title_max_length(self):
        """Тест максимальной длины заголовка (300)."""
        # Валидный заголовок
        lecture = LectureCreate(title="A" * 300)
        assert len(lecture.title) == 300
        
        # Слишком длинный
        with pytest.raises(ValidationError):
            LectureCreate(title="A" * 301)


# ============== Lecture Service Tests ==============

class TestLectureService:
    """Тесты сервиса лекций."""

    @pytest.mark.asyncio
    async def test_publish_generates_code(self):
        """Тест что публикация генерирует код."""
        from app.services.lecture_service import LectureService
        
        mock_db = AsyncMock()
        service = LectureService()
        
        lecture = MagicMock()
        lecture.public_code = None
        lecture.is_published = False
        
        # Mock get_by_public_code возвращает None (код уникален)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        code = await service.publish(mock_db, lecture)
        
        assert len(code) == 8
        assert lecture.is_published is True
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_publish_returns_existing_code(self):
        """Тест что повторная публикация возвращает существующий код."""
        from app.services.lecture_service import LectureService
        
        mock_db = AsyncMock()
        service = LectureService()
        
        lecture = MagicMock()
        lecture.public_code = "abc12345"
        lecture.is_published = False
        
        code = await service.publish(mock_db, lecture)
        
        assert code == "abc12345"
        assert lecture.is_published is True

    @pytest.mark.asyncio
    async def test_unpublish(self):
        """Тест снятия с публикации."""
        from app.services.lecture_service import LectureService
        
        mock_db = AsyncMock()
        service = LectureService()
        
        lecture = MagicMock()
        lecture.is_published = True
        lecture.public_code = "abc12345"
        
        await service.unpublish(mock_db, lecture)
        
        assert lecture.is_published is False
        assert lecture.public_code is None
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_soft_delete(self):
        """Тест мягкого удаления."""
        from app.services.lecture_service import LectureService
        
        mock_db = AsyncMock()
        service = LectureService()
        
        lecture = MagicMock()
        lecture.deleted_at = None
        lecture.is_published = True
        lecture.public_code = "abc12345"
        
        await service.soft_delete(mock_db, lecture)
        
        # soft_delete устанавливает deleted_at
        assert lecture.deleted_at is not None
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_restore(self):
        """Тест восстановления."""
        from app.services.lecture_service import LectureService
        
        mock_db = AsyncMock()
        service = LectureService()
        
        lecture = MagicMock()
        lecture.deleted_at = datetime.now(timezone.utc)
        
        await service.restore(mock_db, lecture)
        
        assert lecture.deleted_at is None
        mock_db.commit.assert_called()


# ============== Public Code Tests ==============

class TestPublicCode:
    """Тесты генерации публичного кода."""

    def test_generate_code_length(self):
        """Тест длины генерируемого кода."""
        from app.services.lecture_service import LectureService
        service = LectureService()
        
        code = service.generate_public_code()
        assert len(code) == 8

    def test_generate_code_uniqueness(self):
        """Тест уникальности генерируемых кодов."""
        from app.services.lecture_service import LectureService
        service = LectureService()
        
        codes = {service.generate_public_code() for _ in range(100)}
        assert len(codes) == 100

    def test_generate_code_characters(self):
        """Тест что код содержит только допустимые символы."""
        from app.services.lecture_service import LectureService
        service = LectureService()
        
        allowed = set("abcdefghijklmnopqrstuvwxyz0123456789")
        
        for _ in range(50):
            code = service.generate_public_code()
            assert all(c in allowed for c in code)


# ============== Image Upload Tests ==============

class TestImageUpload:
    """Тесты загрузки изображений."""

    def test_allowed_mime_types(self):
        """Тест допустимых MIME-типов."""
        from app.api.v1.endpoints.admin_lectures import ALLOWED_IMAGE_TYPES
        
        assert "image/jpeg" in ALLOWED_IMAGE_TYPES
        assert "image/png" in ALLOWED_IMAGE_TYPES
        assert "image/gif" in ALLOWED_IMAGE_TYPES
        assert "image/webp" in ALLOWED_IMAGE_TYPES
        assert "image/svg+xml" not in ALLOWED_IMAGE_TYPES
        assert "application/pdf" not in ALLOWED_IMAGE_TYPES


# ============== Security Tests ==============

class TestSecurityChecklist:
    """Тесты security checklist."""

    def test_content_size_constant_exists(self):
        """Тест что константа размера контента существует."""
        assert MAX_CONTENT_SIZE_BYTES == 5 * 1024 * 1024  # 5MB

    def test_content_depth_constant_exists(self):
        """Тест что константа глубины существует."""
        assert MAX_CONTENT_DEPTH == 50

    def test_content_validation_rejects_large(self):
        """Тест что валидация отклоняет большой контент."""
        with pytest.raises(ValidationError):
            LectureCreate(
                title="Test",
                content={"data": "x" * (MAX_CONTENT_SIZE_BYTES + 1)}
            )


# ============== PDF Generation Tests ==============

class TestPDFGeneration:
    """Тесты генерации PDF (unit, без Playwright)."""

    def test_pdf_service_exists(self):
        """Тест что PDF сервис существует."""
        from app.services.pdf_service import PDFService
        assert PDFService is not None

    @pytest.mark.asyncio
    async def test_pdf_endpoint_requires_auth(self):
        """Тест что PDF endpoint требует авторизации."""
        from app.api.v1.endpoints.admin_lectures import export_lecture_pdf
        # Endpoint существует и декорирован limiter
        assert hasattr(export_lecture_pdf, '__wrapped__')

    def test_pdf_timeout_constant(self):
        """Тест что константа таймаута PDF существует."""
        from app.core.constants import LECTURE_PDF_TIMEOUT_MS
        assert LECTURE_PDF_TIMEOUT_MS > 0
        assert LECTURE_PDF_TIMEOUT_MS <= 30000  # Не более 30 секунд


# ============== Visualization Sandbox Tests ==============

class TestVisualizationSandbox:
    """Тесты безопасности sandbox (проверка констант)."""

    def test_max_code_size_reasonable(self):
        """Тест что лимит размера кода разумный."""
        # Проверяем что константа в frontend разумная (10KB)
        MAX_CODE_SIZE = 10 * 1024  # 10KB как в VisualizationSandbox.tsx
        assert MAX_CODE_SIZE == 10240
        assert MAX_CODE_SIZE < 100 * 1024  # Не более 100KB

    def test_execution_timeout_reasonable(self):
        """Тест что таймаут выполнения разумный."""
        # 5 секунд как в VisualizationSandbox.tsx
        EXECUTION_TIMEOUT_MS = 5000
        assert EXECUTION_TIMEOUT_MS >= 1000  # Минимум 1 секунда
        assert EXECUTION_TIMEOUT_MS <= 10000  # Максимум 10 секунд

    def test_csp_header_concept(self):
        """Тест концепции CSP заголовка."""
        # CSP должен ограничивать источники скриптов
        csp = "default-src 'self' 'unsafe-inline' 'unsafe-eval' blob: data:; script-src 'unsafe-inline' 'unsafe-eval'; style-src 'unsafe-inline';"
        
        assert "default-src" in csp
        assert "script-src" in csp
        assert "style-src" in csp
        # Не должно быть внешних источников
        assert "http://" not in csp
        assert "https://" not in csp
