"""
Парсер расписания с kis.vgltu.ru
"""
import logging
from datetime import date, timedelta

from app.services.external_api import ExternalAPIError, kis_client
from app.services.html_parser import ParsedLesson, ScheduleHtmlParser
from app.services.schedule_constants import PARSE_STEP_DAYS

logger = logging.getLogger(__name__)

# Re-export для обратной совместимости
__all__ = ['ParsedLesson', 'ScheduleParser', 'schedule_parser', 'get_parser']


class ScheduleParser:
    """Парсер расписания ВГЛТУ"""

    def __init__(self):
        self._html_parser = ScheduleHtmlParser()

    async def fetch_schedule(self, teacher_name: str, target_date: date) -> str:
        """Получить HTML расписания на дату"""
        path = f"/schedule?teacher={teacher_name}&date={target_date.isoformat()}"
        logger.info(f"Fetching schedule: {path}")

        try:
            return await kis_client.get(path)
        except ExternalAPIError as e:
            logger.error(f"Failed to fetch schedule: {e}")
            raise RuntimeError(str(e))

    def parse_html(self, html_content: str) -> list[ParsedLesson]:
        """Парсинг HTML расписания (делегирует в ScheduleHtmlParser)"""
        return self._html_parser.parse(html_content)

    async def parse_range(
        self,
        teacher_name: str,
        start_date: date,
        end_date: date,
        progress_callback=None
    ) -> list[ParsedLesson]:
        """Парсинг расписания за период"""
        all_lessons = []
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        processed = 0

        # API возвращает расписание на 2 недели от указанной даты
        while current_date <= end_date:
            try:
                html_content = await self.fetch_schedule(teacher_name, current_date)

                if not html_content or not html_content.strip():
                    logger.warning(f"Empty response for {current_date}")
                    processed += PARSE_STEP_DAYS
                    if progress_callback:
                        progress = min(100, int(processed / total_days * 100))
                        await progress_callback(progress)
                    current_date += timedelta(days=PARSE_STEP_DAYS)
                    continue

                lessons = self.parse_html(html_content)

                for lesson in lessons:
                    if start_date <= lesson.date <= end_date:
                        all_lessons.append(lesson)

                processed += PARSE_STEP_DAYS
                if progress_callback:
                    progress = min(100, int(processed / total_days * 100))
                    await progress_callback(progress)

            except Exception as e:
                logger.error(f"Error fetching schedule for {current_date}: {e}")

            current_date += timedelta(days=PARSE_STEP_DAYS)

        return self._deduplicate(all_lessons)

    def _deduplicate(self, lessons: list[ParsedLesson]) -> list[ParsedLesson]:
        """Убрать дубликаты занятий"""
        seen = set()
        unique = []
        for lesson in lessons:
            key = (lesson.date, lesson.lesson_number, tuple(lesson.groups), lesson.subgroup)
            if key not in seen:
                seen.add(key)
                unique.append(lesson)
        logger.info(f"Parsed {len(unique)} unique lessons")
        return unique


# Singleton instance
schedule_parser = ScheduleParser()


async def get_parser() -> ScheduleParser:
    """Для обратной совместимости."""
    return schedule_parser


class SyncScheduleParser:
    """
    Синхронный парсер расписания для Celery tasks.
    Использует requests вместо httpx async.
    """

    def __init__(self):
        self._html_parser = ScheduleHtmlParser()
        self._base_url = "https://kis.vgltu.ru"
        self._timeout = 30

    def fetch_schedule(self, teacher_name: str, target_date: date) -> str:
        """Получить HTML расписания на дату (синхронно)"""
        import requests
        from tenacity import retry, stop_after_attempt, wait_exponential

        url = f"{self._base_url}/schedule"
        params = {"teacher": teacher_name, "date": target_date.isoformat()}

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
        def _fetch():
            response = requests.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()
            return response.text

        try:
            return _fetch()
        except Exception as e:
            logger.error(f"Failed to fetch schedule: {e}")
            raise RuntimeError(str(e))

    def parse_range(
        self,
        teacher_name: str,
        start_date: date,
        end_date: date
    ) -> list[ParsedLesson]:
        """Парсинг расписания за период (синхронно)"""
        all_lessons = []
        current_date = start_date

        while current_date <= end_date:
            try:
                html_content = self.fetch_schedule(teacher_name, current_date)

                if html_content and html_content.strip():
                    lessons = self._html_parser.parse(html_content)
                    for lesson in lessons:
                        if start_date <= lesson.date <= end_date:
                            all_lessons.append(lesson)

            except Exception as e:
                logger.error(f"Error fetching schedule for {current_date}: {e}")

            current_date += timedelta(days=PARSE_STEP_DAYS)

        return self._deduplicate(all_lessons)

    def _deduplicate(self, lessons: list[ParsedLesson]) -> list[ParsedLesson]:
        """Убрать дубликаты занятий"""
        seen = set()
        unique = []
        for lesson in lessons:
            key = (lesson.date, lesson.lesson_number, tuple(lesson.groups), lesson.subgroup)
            if key not in seen:
                seen.add(key)
                unique.append(lesson)
        return unique

    def parse_and_import_sync(
        self,
        db,
        teacher_name: str,
        start_date: date,
        end_date: date
    ) -> dict:
        """
        Парсинг и импорт расписания в БД (синхронно).
        Упрощённая версия для Celery tasks.
        """
        from sqlalchemy import select

        from app.models.group import Group
        from app.models.lesson import Lesson
        from app.models.schedule import LessonType
        from app.services.schedule_constants import LESSON_TIMES

        parsed_lessons = self.parse_range(teacher_name, start_date, end_date)

        stats = {
            "total_parsed": len(parsed_lessons),
            "lessons_created": 0,
            "lessons_skipped": 0,
            "conflicts_created": 0,
            "groups": set(),
        }

        for parsed in parsed_lessons:
            for group_name in parsed.groups:
                stats["groups"].add(group_name)

                # Получаем или создаём группу
                result = db.execute(select(Group).where(Group.name == group_name))
                group = result.scalar_one_or_none()

                if not group:
                    code = group_name.replace("-", "").replace(" ", "").upper()[:8]
                    group = Group(name=group_name, code=code)
                    db.add(group)
                    db.flush()

                # Проверяем существование занятия
                existing = db.execute(
                    select(Lesson).where(
                        Lesson.group_id == group.id,
                        Lesson.date == parsed.date,
                        Lesson.lesson_number == parsed.lesson_number,
                        Lesson.subgroup == parsed.subgroup
                    )
                ).scalar_one_or_none()

                if existing:
                    stats["lessons_skipped"] += 1
                    continue

                # Создаём занятие
                start_time, end_time = LESSON_TIMES.get(parsed.lesson_number, ("09:00", "10:30"))

                lesson = Lesson(
                    group_id=group.id,
                    date=parsed.date,
                    lesson_number=parsed.lesson_number,
                    subgroup=parsed.subgroup,
                    topic=parsed.subject or "",
                    lesson_type=LessonType(parsed.lesson_type) if parsed.lesson_type else LessonType.LECTURE,
                    room=parsed.room,
                    start_time=start_time,
                    end_time=end_time,
                )
                db.add(lesson)
                stats["lessons_created"] += 1

        db.commit()
        stats["groups"] = list(stats["groups"])
        return stats


# Синхронный singleton
_sync_parser = None


def get_parser_sync() -> SyncScheduleParser:
    """Получить синхронный парсер для Celery tasks."""
    global _sync_parser
    if _sync_parser is None:
        _sync_parser = SyncScheduleParser()
    return _sync_parser
