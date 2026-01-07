"""
Сервис импорта расписания в БД
"""
import logging
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.services.schedule_parser import get_parser, ParsedLesson
from app.services.lesson_importer import LessonImporter
from app.services.semester_utils import get_semester, detect_semester_end, find_teacher
from app.crud.crud_subject import get_or_create_subject, get_or_create_assignment_from_schedule

logger = logging.getLogger(__name__)


class ScheduleImportService:
    """Сервис импорта расписания"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._lesson_importer = LessonImporter(db)
    
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
    
    async def import_from_parser(
        self,
        teacher_name: str,
        start_date: date,
        end_date: date,
        progress_callback=None,
        smart_update: bool = True
    ) -> dict:
        """Импорт расписания из парсера с транзакцией"""
        parser = await get_parser()
        
        parsed_lessons = await parser.parse_range(
            teacher_name, start_date, end_date, progress_callback
        )
        
        semester = get_semester(start_date)
        teacher = await find_teacher(self.db, teacher_name)
        
        stats = self._init_stats(len(parsed_lessons))
        
        # Автоопределение конца семестра
        semester_end_info = detect_semester_end(parsed_lessons, start_date, end_date)
        if semester_end_info["detected"]:
            stats["semester_end_detected"] = True
            stats["last_lesson_date"] = semester_end_info["last_lesson_date"]
            stats["empty_weeks_count"] = semester_end_info["empty_weeks"]
            logger.info(f"Semester end detected: last lesson {semester_end_info['last_lesson_date']}")
        
        group_parsed_keys: dict[str, set] = {}
        
        try:
            for parsed in parsed_lessons:
                await self._process_lesson(
                    parsed, teacher, semester, smart_update, stats, group_parsed_keys
                )
            
            # Обнаруживаем удалённые занятия
            if smart_update:
                for group_name, parsed_keys in group_parsed_keys.items():
                    group = await self.get_or_create_group(group_name)
                    deleted = await self._lesson_importer.detect_deleted(
                        group, start_date, end_date, parsed_keys
                    )
                    stats["conflicts_created"] += deleted
            
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Import failed, rolled back: {e}")
            raise
        
        stats["groups_created"] = len(stats["groups"])
        stats["groups"] = list(stats["groups"])
        stats["subjects"] = list(stats["subjects"])
        
        logger.info(f"Import complete: {stats}")
        return stats
    
    def _init_stats(self, total_parsed: int) -> dict:
        """Инициализировать статистику"""
        return {
            "total_parsed": total_parsed,
            "groups_created": 0,
            "lessons_created": 0,
            "lessons_skipped": 0,
            "conflicts_created": 0,
            "subjects_created": 0,
            "assignments_created": 0,
            "groups": set(),
            "subjects": set(),
            "semester_end_detected": False,
            "last_lesson_date": None,
            "empty_weeks_count": 0,
        }
    
    async def _process_lesson(
        self,
        parsed: ParsedLesson,
        teacher: Optional[object],
        semester: str,
        smart_update: bool,
        stats: dict,
        group_parsed_keys: dict
    ):
        """Обработать одно занятие"""
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
                result = await self._lesson_importer.import_smart(parsed, group, subject_id)
                if result["action"] == "created":
                    stats["lessons_created"] += 1
                elif result["action"] == "skipped":
                    stats["lessons_skipped"] += 1
                elif result["action"] == "conflict":
                    stats["conflicts_created"] += 1
            else:
                lesson = await self._lesson_importer.import_simple(parsed, group, subject_id)
                if lesson:
                    stats["lessons_created"] += 1
                else:
                    stats["lessons_skipped"] += 1
