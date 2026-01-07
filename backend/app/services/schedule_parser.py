"""
Парсер расписания с kis.vgltu.ru
"""
import logging
from datetime import date, timedelta

from app.services.external_api import kis_client, ExternalAPIError
from app.services.schedule_constants import PARSE_STEP_DAYS
from app.services.html_parser import ScheduleHtmlParser, ParsedLesson

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
