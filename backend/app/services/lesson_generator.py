"""
Сервис генерации занятий из расписания.
"""
import logging
from datetime import date, timedelta
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import ScheduleItem, DayOfWeek, WeekParity
from app.models.lesson import Lesson
from app.crud.crud_schedule import schedule as schedule_crud, lesson as lesson_crud

logger = logging.getLogger(__name__)

# Маппинг дней недели Python -> enum
WEEKDAY_MAP = {
    0: DayOfWeek.MONDAY,
    1: DayOfWeek.TUESDAY,
    2: DayOfWeek.WEDNESDAY,
    3: DayOfWeek.THURSDAY,
    4: DayOfWeek.FRIDAY,
    5: DayOfWeek.SATURDAY,
}


class LessonGenerator:
    """Генерация занятий из расписания"""
    
    async def generate_lessons_for_period(
        self,
        db: AsyncSession,
        group_id: UUID,
        start_date: date,
        end_date: date
    ) -> List[Lesson]:
        """
        Генерирует занятия на период по расписанию.
        Учитывает:
        - День недели
        - Чётность недели
        - Период действия расписания
        """
        schedule_items = await schedule_crud.get_by_group(db, group_id, active_only=True)
        
        if not schedule_items:
            logger.warning(f"No schedule items for group {group_id}")
            return []
        
        lessons = []
        current = start_date
        
        while current <= end_date:
            weekday = current.weekday()
            if weekday > 5:  # Воскресенье пропускаем
                current += timedelta(days=1)
                continue
            
            day_of_week = WEEKDAY_MAP.get(weekday)
            if not day_of_week:
                current += timedelta(days=1)
                continue
            
            # Определяем чётность недели
            week_number = current.isocalendar()[1]
            week_parity = WeekParity.ODD if week_number % 2 else WeekParity.EVEN
            
            for item in schedule_items:
                # Проверяем день недели
                if item.day_of_week != day_of_week:
                    continue
                
                # Проверяем чётность недели
                if item.week_parity and item.week_parity != week_parity:
                    continue
                
                # Проверяем период действия
                if item.start_date > current:
                    continue
                if item.end_date and item.end_date < current:
                    continue
                
                # Создаём занятие
                lesson = await lesson_crud.create(
                    db,
                    group_id=group_id,
                    schedule_item_id=item.id,
                    date=current,
                    lesson_number=item.lesson_number,
                    lesson_type=item.lesson_type,
                    subgroup=item.subgroup
                )
                lessons.append(lesson)
            
            current += timedelta(days=1)
        
        logger.info(f"Generated {len(lessons)} lessons for group {group_id}")
        return lessons


lesson_generator = LessonGenerator()
