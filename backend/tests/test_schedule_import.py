"""
Тесты для импорта расписания.
"""
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.v1.endpoints.admin_schedule import ParseScheduleResponse
from app.api.v1.endpoints.admin_schedule_parser import parse_now
from app.services.html_parser import ParsedLesson
from app.services.schedule_parser import SyncScheduleParser
from app.services.semester_utils import detect_semester_end, get_semester


class TestSemesterEndDetection:
    """test_semester_end_detection — определение конца семестра"""

    def test_no_lessons(self):
        """Пустой список занятий"""
        result = detect_semester_end([], date(2025, 1, 1), date(2025, 1, 31))
        assert not result["detected"]
        assert result["last_lesson_date"] is None

    def test_lessons_until_end(self):
        """Занятия до конца периода"""
        lessons = [
            MagicMock(date=date(2025, 1, 15)),
            MagicMock(date=date(2025, 1, 29)),
        ]
        result = detect_semester_end(lessons, date(2025, 1, 1), date(2025, 1, 31))

        assert not result["detected"]
        assert result["empty_weeks"] < 2

    def test_semester_end_detected(self):
        """Обнаружение конца семестра (2+ пустых недели)"""
        lessons = [
            MagicMock(date=date(2025, 1, 10)),
            MagicMock(date=date(2025, 1, 15)),
        ]
        # Период до 15 февраля — больше 2 недель после последнего занятия
        result = detect_semester_end(lessons, date(2025, 1, 1), date(2025, 2, 15))

        assert result["detected"]
        assert result["empty_weeks"] >= 2
        assert result["last_lesson_date"] == "2025-01-15"


class TestGetSemester:
    """Тест определения семестра"""

    def test_fall_semester(self):
        """Осенний семестр (сентябрь-декабрь)"""
        assert get_semester(date(2025, 9, 1)) == "2025-1"
        assert get_semester(date(2025, 12, 15)) == "2025-1"

    def test_spring_semester(self):
        """Весенний семестр (февраль-июнь)"""
        assert get_semester(date(2025, 2, 1)) == "2025-2"
        assert get_semester(date(2025, 6, 15)) == "2025-2"

    def test_january_is_fall(self):
        """Январь относится к осеннему семестру предыдущего года"""
        assert get_semester(date(2025, 1, 15)) == "2024-1"


class TestConflictDetection:
    """test_conflict_detection — обнаружение изменений"""

    @pytest.mark.asyncio
    async def test_detect_topic_change(self):
        """Обнаружение изменения темы"""
        from app.models.schedule import LessonType
        from app.services.lesson_importer import LessonImporter

        # Mock DB session
        db = MagicMock()
        db.add = MagicMock()
        db.add = MagicMock()

        # Mock existing lesson
        existing_lesson = MagicMock()
        existing_lesson.id = uuid4()
        existing_lesson.topic = "Старая тема"
        existing_lesson.lesson_type = LessonType.LECTURE

        # Правильный mock для async execute
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_lesson
        db.execute = AsyncMock(return_value=mock_result)

        importer = LessonImporter(db)

        # Parsed lesson с новой темой
        parsed = MagicMock()
        parsed.date = date(2025, 1, 15)
        parsed.lesson_number = 1
        parsed.lesson_type = "lecture"
        parsed.subject = "Новая тема"
        parsed.subgroup = None

        group = MagicMock()
        group.id = uuid4()

        result = await importer.import_smart(parsed, group)

        assert result["action"] == "conflict"
        # Проверяем что конфликт добавлен в сессию
        assert db.add.called


class TestDeletedLessonDetection:
    """test_deleted_lesson_detection — обнаружение удалений"""

    @pytest.mark.asyncio
    async def test_detect_deleted_lesson(self):
        """Обнаружение удалённого занятия"""
        from app.models.schedule import LessonType
        from app.services.lesson_importer import LessonImporter

        db = MagicMock()
        db.add = MagicMock()

        # Существующее занятие в БД
        existing_lesson = MagicMock()
        existing_lesson.id = uuid4()
        existing_lesson.date = date(2025, 1, 15)
        existing_lesson.lesson_number = 1
        existing_lesson.subgroup = None
        existing_lesson.topic = "Тема"
        existing_lesson.lesson_type = LessonType.LECTURE

        # Правильный mock для async execute
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [existing_lesson]
        mock_result.scalars.return_value = mock_scalars
        db.execute = AsyncMock(return_value=mock_result)

        importer = LessonImporter(db)

        group = MagicMock()
        group.id = uuid4()

        # Пустой set — занятие исчезло из расписания
        parsed_keys = set()

        count = await importer.detect_deleted(
            group,
            date(2025, 1, 1),
            date(2025, 1, 31),
            parsed_keys
        )

        assert count == 1
        assert db.add.called


class TestAutoParserSyncImport:
    """Проверки sync-ветки автопарсера."""

    def test_sync_parser_import_creates_lessons_without_legacy_fields(self):
        parser = SyncScheduleParser()
        group_id = uuid4()

        parser.parse_range = MagicMock(
            return_value=[
                ParsedLesson(
                    date=date(2026, 3, 12),
                    lesson_number=2,
                    lesson_type="lecture",
                    subject="Математика",
                    groups=["ИС-241"],
                    subgroup=None,
                    room="101",
                )
            ]
        )

        first_result = MagicMock()
        first_result.scalar_one_or_none.return_value = None
        second_result = MagicMock()
        second_result.scalar_one_or_none.return_value = None

        db = MagicMock()
        db.execute.side_effect = [first_result, second_result]

        created_objects = []

        def capture_add(obj):
            created_objects.append(obj)

        def assign_group_id():
            created_group = created_objects[-1]
            created_group.id = group_id

        db.add.side_effect = capture_add
        db.flush.side_effect = assign_group_id

        stats = parser.parse_and_import_sync(db, "Миронов Г.Д.", date(2026, 3, 12), date(2026, 3, 12))

        lesson = created_objects[-1]

        assert lesson.group_id == group_id
        assert lesson.date == date(2026, 3, 12)
        assert lesson.lesson_number == 2
        assert lesson.topic == "Математика"
        assert stats["groups_created"] == 1
        assert stats["lessons_created"] == 1
        assert stats["lessons_updated"] == 0
        db.commit.assert_called_once()


class TestManualParseEndpoint:
    """Проверки ручного запуска парсинга."""

    @pytest.mark.asyncio
    async def test_parse_now_writes_history_and_returns_stats(self):
        db = AsyncMock()
        db.add = MagicMock()
        user = SimpleNamespace(id=uuid4())
        config = SimpleNamespace(id=uuid4(), teacher_name="Миронов Г.Д.", parse_days_ahead=14, last_run_at=None)
        history = SimpleNamespace(id=uuid4())
        stats = {
            "total_parsed": 2,
            "groups_created": 1,
            "lessons_created": 2,
            "lessons_updated": 0,
            "lessons_skipped": 0,
            "conflicts_created": 0,
            "groups": ["ИС-241"],
            "subjects": ["Математика"],
        }

        with (
            patch("app.api.v1.endpoints.admin_schedule_parser.crud.get_parser_config", AsyncMock(return_value=config)),
            patch(
                "app.api.v1.endpoints.admin_schedule_parser.crud_parse_history.create_history",
                AsyncMock(return_value=history),
            ),
            patch(
                "app.api.v1.endpoints.admin_schedule_parser.crud_parse_history.complete_history", AsyncMock()
            ) as complete_history,
            patch("app.api.v1.endpoints.admin_schedule_parser.ScheduleImportService") as service_cls,
        ):
            service_cls.return_value.import_from_parser = AsyncMock(return_value=stats)

            result = await parse_now(db=db, current_user=user)

        assert result == stats
        complete_history.assert_awaited_once_with(db, history.id, stats)
        assert db.commit.await_count == 2
        assert config.last_run_at is not None

    def test_parse_schedule_response_accepts_extended_stats(self):
        response = ParseScheduleResponse(
            total_parsed=5,
            groups_created=2,
            lessons_created=3,
            lessons_updated=0,
            lessons_skipped=2,
            conflicts_created=1,
            subjects_created=1,
            assignments_created=1,
            groups=["ИС-241"],
            subjects=["Математика"],
            semester_end_detected=True,
            last_lesson_date="2026-03-14",
            empty_weeks_count=2,
        )

        assert response.subjects == ["Математика"]
        assert response.conflicts_created == 1
        assert response.semester_end_detected is True
