"""
Импорт занятий в БД с обнаружением конфликтов
"""
import logging
from datetime import date
from uuid import UUID
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.models.schedule_conflict import ScheduleConflict, ConflictType
from app.services.html_parser import ParsedLesson
from app.services.schedule_constants import LESSON_TYPE_ENUM_MAP

logger = logging.getLogger(__name__)


class LessonImporter:
    """Импортер занятий с обнаружением конфликтов"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def import_smart(
        self, 
        parsed: ParsedLesson, 
        group: Group, 
        subject_id: Optional[UUID] = None
    ) -> dict:
        """
        Умный импорт занятия с обнаружением конфликтов.
        Returns: {"action": "created"|"skipped"|"conflict", "lesson": Lesson|None}
        """
        lesson_type = LESSON_TYPE_ENUM_MAP.get(parsed.lesson_type, LessonType.LECTURE)
        
        existing = await self._find_existing(group.id, parsed)
        
        if not existing:
            lesson = self._create_lesson(parsed, group, lesson_type, subject_id)
            self.db.add(lesson)
            return {"action": "created", "lesson": lesson}
        
        changes = self._detect_changes(existing, parsed, lesson_type)
        
        if not changes:
            return {"action": "skipped", "lesson": existing}
        
        await self._create_conflict(existing, parsed, lesson_type)
        return {"action": "conflict", "lesson": existing}
    
    async def import_simple(
        self, 
        parsed: ParsedLesson, 
        group: Group, 
        subject_id: Optional[UUID] = None
    ) -> Optional[Lesson]:
        """Импортировать одно занятие (без конфликтов)"""
        existing = await self._find_existing(group.id, parsed)
        
        if existing:
            return None
        
        lesson_type = LESSON_TYPE_ENUM_MAP.get(parsed.lesson_type, LessonType.LECTURE)
        lesson = self._create_lesson(parsed, group, lesson_type, subject_id)
        self.db.add(lesson)
        return lesson
    
    async def detect_deleted(
        self,
        group: Group,
        start_date: date,
        end_date: date,
        parsed_keys: set
    ) -> int:
        """
        Обнаружить занятия, которые исчезли из расписания.
        parsed_keys: set of (date, lesson_number, subgroup) tuples
        """
        result = await self.db.execute(
            select(Lesson).where(
                Lesson.group_id == group.id,
                Lesson.date >= start_date,
                Lesson.date <= end_date,
                Lesson.is_cancelled == False
            )
        )
        existing_lessons = result.scalars().all()
        
        conflicts_created = 0
        for lesson in existing_lessons:
            key = (lesson.date, lesson.lesson_number, lesson.subgroup)
            if key not in parsed_keys:
                await self._create_deleted_conflict(lesson)
                conflicts_created += 1
                logger.info(f"Lesson {lesson.id} disappeared from schedule")
        
        return conflicts_created
    
    async def _find_existing(self, group_id: UUID, parsed: ParsedLesson) -> Optional[Lesson]:
        """Найти существующее занятие"""
        result = await self.db.execute(
            select(Lesson).where(
                Lesson.group_id == group_id,
                Lesson.date == parsed.date,
                Lesson.lesson_number == parsed.lesson_number,
                Lesson.subgroup == parsed.subgroup
            )
        )
        return result.scalar_one_or_none()
    
    def _create_lesson(
        self, 
        parsed: ParsedLesson, 
        group: Group, 
        lesson_type: LessonType,
        subject_id: Optional[UUID]
    ) -> Lesson:
        """Создать объект занятия"""
        return Lesson(
            group_id=group.id,
            date=parsed.date,
            lesson_number=parsed.lesson_number,
            lesson_type=lesson_type,
            topic=parsed.subject,
            subgroup=parsed.subgroup,
            is_cancelled=False,
            subject_id=subject_id
        )
    
    def _detect_changes(self, existing: Lesson, parsed: ParsedLesson, lesson_type: LessonType) -> dict:
        """Обнаружить изменения между существующим и новым занятием"""
        changes = {}
        if existing.topic != parsed.subject:
            changes["topic"] = {"old": existing.topic, "new": parsed.subject}
        if existing.lesson_type != lesson_type:
            changes["lesson_type"] = {"old": existing.lesson_type.value, "new": lesson_type.value}
        return changes
    
    async def _create_conflict(self, existing: Lesson, parsed: ParsedLesson, lesson_type: LessonType):
        """Создать конфликт изменения"""
        old_data = {
            "topic": existing.topic,
            "lesson_type": existing.lesson_type.value,
            "date": str(existing.date),
            "lesson_number": existing.lesson_number
        }
        new_data = {
            "topic": parsed.subject,
            "lesson_type": lesson_type.value,
            "date": str(parsed.date),
            "lesson_number": parsed.lesson_number
        }
        
        conflict = ScheduleConflict(
            lesson_id=existing.id,
            conflict_type=ConflictType.CHANGED.value,
            old_data=old_data,
            new_data=new_data
        )
        self.db.add(conflict)
        logger.info(f"Conflict detected for lesson {existing.id}")
    
    async def _create_deleted_conflict(self, lesson: Lesson):
        """Создать конфликт удаления"""
        old_data = {
            "topic": lesson.topic,
            "lesson_type": lesson.lesson_type.value,
            "date": str(lesson.date),
            "lesson_number": lesson.lesson_number
        }
        conflict = ScheduleConflict(
            lesson_id=lesson.id,
            conflict_type=ConflictType.DELETED.value,
            old_data=old_data,
            new_data=None
        )
        self.db.add(conflict)
