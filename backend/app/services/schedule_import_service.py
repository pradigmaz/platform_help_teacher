"""
Сервис импорта расписания в БД
"""
import logging
from datetime import date
from uuid import UUID
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.models.user import User, UserRole
from app.models.schedule_conflict import ScheduleConflict, ConflictType
from app.services.schedule_parser import ParsedLesson, get_parser
from app.crud.crud_subject import get_or_create_subject, get_or_create_assignment_from_schedule

logger = logging.getLogger(__name__)

LESSON_TYPE_MAP = {
    "lecture": LessonType.LECTURE,
    "lab": LessonType.LAB,
    "practice": LessonType.PRACTICE,
}


class ScheduleImportService:
    """Сервис импорта расписания"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_group(self, group_name: str) -> Group:
        """Получить или создать группу"""
        result = await self.db.execute(
            select(Group).where(Group.name == group_name)
        )
        group = result.scalar_one_or_none()
        
        if not group:
            code = group_name.replace("-", "").replace(" ", "").upper()[:8]
            group = Group(name=group_name, code=code)
            self.db.add(group)
            await self.db.flush()
            logger.info(f"Created group: {group_name}")
        
        return group
    
    async def import_lesson_smart(
        self, 
        parsed: ParsedLesson, 
        group: Group, 
        subject_id: Optional[UUID] = None
    ) -> dict:
        """
        Умный импорт занятия с обнаружением конфликтов.
        Returns: {"action": "created"|"skipped"|"conflict", "lesson": Lesson|None}
        """
        lesson_type = LESSON_TYPE_MAP.get(parsed.lesson_type, LessonType.LECTURE)
        
        # Ищем существующее занятие
        result = await self.db.execute(
            select(Lesson).where(
                Lesson.group_id == group.id,
                Lesson.date == parsed.date,
                Lesson.lesson_number == parsed.lesson_number,
                Lesson.subgroup == parsed.subgroup
            )
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            # Новое занятие - создаём
            lesson = Lesson(
                group_id=group.id,
                date=parsed.date,
                lesson_number=parsed.lesson_number,
                lesson_type=lesson_type,
                topic=parsed.subject,
                subgroup=parsed.subgroup,
                is_cancelled=False,
                subject_id=subject_id
            )
            self.db.add(lesson)
            return {"action": "created", "lesson": lesson}
        
        # Занятие существует - проверяем изменения
        changes = {}
        if existing.topic != parsed.subject:
            changes["topic"] = {"old": existing.topic, "new": parsed.subject}
        if existing.lesson_type != lesson_type:
            changes["lesson_type"] = {"old": existing.lesson_type.value, "new": lesson_type.value}
        
        if not changes:
            # Без изменений
            return {"action": "skipped", "lesson": existing}
        
        # Есть изменения - создаём конфликт
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
        logger.info(f"Conflict detected for lesson {existing.id}: {changes}")
        
        return {"action": "conflict", "lesson": existing}
    
    async def detect_deleted_lessons(
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
                # Занятие исчезло - создаём конфликт
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
                conflicts_created += 1
                logger.info(f"Lesson {lesson.id} disappeared from schedule")
        
        return conflicts_created
    
    async def import_from_parser(
        self,
        teacher_name: str,
        start_date: date,
        end_date: date,
        progress_callback=None,
        smart_update: bool = True
    ) -> dict:
        """Импорт расписания из парсера"""
        parser = await get_parser()
        
        parsed_lessons = await parser.parse_range(
            teacher_name, start_date, end_date, progress_callback
        )
        
        semester = self._get_semester(start_date)
        teacher = await self._find_teacher(teacher_name)
        
        stats = {
            "total_parsed": len(parsed_lessons),
            "groups_created": 0,
            "lessons_created": 0,
            "lessons_skipped": 0,
            "conflicts_created": 0,
            "subjects_created": 0,
            "assignments_created": 0,
            "groups": set(),
            "subjects": set()
        }
        
        # Собираем ключи спарсенных занятий для каждой группы
        group_parsed_keys: dict[str, set] = {}
        
        for parsed in parsed_lessons:
            subject_id = None
            if parsed.subject:
                subject, created = await get_or_create_subject(self.db, parsed.subject)
                subject_id = subject.id
                stats["subjects"].add(parsed.subject)
                if created:
                    stats["subjects_created"] += 1
            
            for group_name in parsed.groups:
                stats["groups"].add(group_name)
                group = await self.get_or_create_group(group_name)
                
                # Запоминаем ключ занятия
                if group_name not in group_parsed_keys:
                    group_parsed_keys[group_name] = set()
                group_parsed_keys[group_name].add(
                    (parsed.date, parsed.lesson_number, parsed.subgroup)
                )
                
                if teacher and parsed.subject:
                    assignment, created = await get_or_create_assignment_from_schedule(
                        self.db, teacher.id, parsed.subject, group.id, semester
                    )
                    if created:
                        stats["assignments_created"] += 1
                
                if smart_update:
                    result = await self.import_lesson_smart(parsed, group, subject_id)
                    if result["action"] == "created":
                        stats["lessons_created"] += 1
                    elif result["action"] == "skipped":
                        stats["lessons_skipped"] += 1
                    elif result["action"] == "conflict":
                        stats["conflicts_created"] += 1
                else:
                    lesson = await self.import_lesson(parsed, group, subject_id)
                    if lesson:
                        stats["lessons_created"] += 1
                    else:
                        stats["lessons_skipped"] += 1
        
        # Обнаруживаем удалённые занятия
        if smart_update:
            for group_name, parsed_keys in group_parsed_keys.items():
                group = await self.get_or_create_group(group_name)
                deleted = await self.detect_deleted_lessons(
                    group, start_date, end_date, parsed_keys
                )
                stats["conflicts_created"] += deleted
        
        await self.db.commit()
        
        stats["groups_created"] = len(stats["groups"])
        stats["groups"] = list(stats["groups"])
        stats["subjects"] = list(stats["subjects"])
        
        logger.info(f"Import complete: {stats}")
        return stats
    
    async def import_lesson(self, parsed: ParsedLesson, group: Group, subject_id: Optional[UUID] = None) -> Optional[Lesson]:
        """Импортировать одно занятие (старый метод без конфликтов)"""
        result = await self.db.execute(
            select(Lesson).where(
                Lesson.group_id == group.id,
                Lesson.date == parsed.date,
                Lesson.lesson_number == parsed.lesson_number,
                Lesson.subgroup == parsed.subgroup
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return None
        
        lesson_type = LESSON_TYPE_MAP.get(parsed.lesson_type, LessonType.LECTURE)
        
        lesson = Lesson(
            group_id=group.id,
            date=parsed.date,
            lesson_number=parsed.lesson_number,
            lesson_type=lesson_type,
            topic=parsed.subject,
            subgroup=parsed.subgroup,
            is_cancelled=False,
            subject_id=subject_id
        )
        self.db.add(lesson)
        return lesson
    
    def _get_semester(self, d: date) -> str:
        """Определить семестр по дате"""
        year = d.year
        if d.month >= 9:
            return f"{year}-1"
        elif d.month <= 1:
            return f"{year-1}-1"
        else:
            return f"{year}-2"
    
    async def _find_teacher(self, teacher_name: str) -> Optional[User]:
        """Найти преподавателя по имени"""
        result = await self.db.execute(
            select(User).where(
                User.full_name == teacher_name,
                User.role == UserRole.TEACHER
            )
        )
        return result.scalar_one_or_none()
