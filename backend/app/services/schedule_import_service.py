"""
Сервис импорта расписания в БД
"""

import logging
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_subject import get_or_create_assignment_from_schedule
from app.models.group import Group
from app.models.lesson import Lesson
from app.models.subject import Subject
from app.models.user import User
from app.services.lesson_importer import LessonImporter
from app.services.schedule_parser import ParsedLesson, get_parser
from app.services.semester_utils import detect_semester_end, find_teacher, get_semester

logger = logging.getLogger(__name__)


class ScheduleImportService:
    """Сервис импорта расписания"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._lesson_importer = LessonImporter(db)

    async def get_or_create_group(self, group_name: str) -> Group:
        """Получить или создать группу"""
        result = await self.db.execute(select(Group).where(Group.name == group_name))
        group = result.scalar_one_or_none()

        if not group:
            code = group_name.replace("-", "").replace(" ", "").upper()[:8]
            group = Group(name=group_name, code=code)
            self.db.add(group)
            await self.db.flush()
            logger.info(f"Created group: {group_name}")

        return group

    async def _prepare_groups(self, parsed_lessons: list[ParsedLesson]) -> dict[str, Group]:
        group_names = sorted({group_name for parsed in parsed_lessons for group_name in parsed.groups})
        if not group_names:
            return {}

        result = await self.db.execute(select(Group).where(Group.name.in_(group_names)))
        groups_by_name = {group.name: group for group in result.scalars().all()}

        for group_name in group_names:
            if group_name not in groups_by_name:
                code = group_name.replace("-", "").replace(" ", "").upper()[:8]
                group = Group(name=group_name, code=code)
                self.db.add(group)
                groups_by_name[group_name] = group
                logger.info(f"Created group: {group_name}")

        await self.db.flush()
        return groups_by_name

    async def _prepare_subjects(self, parsed_lessons: list[ParsedLesson], stats: dict) -> dict[str, Subject]:
        subject_names = sorted({parsed.subject for parsed in parsed_lessons if parsed.subject})
        if not subject_names:
            return {}

        lowered_names = [name.lower() for name in subject_names]
        result = await self.db.execute(select(Subject).where(func.lower(Subject.name).in_(lowered_names)))
        subjects_by_lower = {subject.name.lower(): subject for subject in result.scalars().all()}

        subjects_by_name: dict[str, Subject] = {}
        for subject_name in subject_names:
            stats["subjects"].add(subject_name)
            subject = subjects_by_lower.get(subject_name.lower())
            if not subject:
                subject = Subject(name=subject_name)
                self.db.add(subject)
                subjects_by_lower[subject_name.lower()] = subject
                stats["subjects_created"] += 1
                logger.info(f"Created subject: {subject_name}")
            subjects_by_name[subject_name] = subject

        await self.db.flush()
        return subjects_by_name

    async def _load_existing_lessons(
        self, groups_by_name: dict[str, Group], start_date: date, end_date: date
    ) -> dict[tuple, Lesson]:
        group_ids = [group.id for group in groups_by_name.values()]
        if not group_ids:
            return {}

        result = await self.db.execute(
            select(Lesson).where(
                Lesson.group_id.in_(group_ids),
                Lesson.date >= start_date,
                Lesson.date <= end_date,
            )
        )
        return {
            (lesson.group_id, lesson.date, lesson.lesson_number, lesson.subgroup): lesson
            for lesson in result.scalars().all()
        }

    async def import_from_parser(
        self, teacher_name: str, start_date: date, end_date: date, progress_callback=None, smart_update: bool = True
    ) -> dict:
        """Импорт расписания из парсера с транзакцией"""
        parser = await get_parser()

        parsed_lessons = await parser.parse_range(teacher_name, start_date, end_date, progress_callback)

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
            groups_by_name = await self._prepare_groups(parsed_lessons)
            subjects_by_name = await self._prepare_subjects(parsed_lessons, stats)
            existing_lessons = await self._load_existing_lessons(groups_by_name, start_date, end_date)
            assignment_cache: set[tuple[str, str]] = set()

            for parsed in parsed_lessons:
                await self._process_lesson(
                    parsed,
                    teacher,
                    semester,
                    smart_update,
                    stats,
                    group_parsed_keys,
                    groups_by_name,
                    subjects_by_name,
                    existing_lessons,
                    assignment_cache,
                )

            # Обнаруживаем удалённые занятия
            if smart_update:
                for group_name, parsed_keys in group_parsed_keys.items():
                    group = groups_by_name[group_name]
                    deleted = await self._lesson_importer.detect_deleted(group, start_date, end_date, parsed_keys)
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
            "lessons_updated": 0,
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
        teacher: User | None,
        semester: str,
        smart_update: bool,
        stats: dict,
        group_parsed_keys: dict,
        groups_by_name: dict[str, Group],
        subjects_by_name: dict[str, Subject],
        existing_lessons: dict[tuple, Lesson],
        assignment_cache: set[tuple[str, str]],
    ) -> None:
        """Обработать одно занятие"""
        subject = subjects_by_name.get(parsed.subject) if parsed.subject else None
        subject_id = subject.id if subject else None

        for group_name in parsed.groups:
            stats["groups"].add(group_name)
            group = groups_by_name[group_name]

            if group_name not in group_parsed_keys:
                group_parsed_keys[group_name] = set()
            group_parsed_keys[group_name].add((parsed.date, parsed.lesson_number, parsed.subgroup))

            if teacher and parsed.subject:
                assignment_key = (group_name, parsed.subject)
                if assignment_key not in assignment_cache:
                    _assignment, created = await get_or_create_assignment_from_schedule(
                        self.db, teacher.id, parsed.subject, group.id, semester
                    )
                    assignment_cache.add(assignment_key)
                    if created:
                        stats["assignments_created"] += 1

            key = (group.id, parsed.date, parsed.lesson_number, parsed.subgroup)
            existing = existing_lessons.get(key)
            if smart_update:
                result = await self._lesson_importer.import_smart(
                    parsed, group, subject_id, existing=existing, existing_loaded=True
                )
                if result["lesson"] is not None:
                    existing_lessons[key] = result["lesson"]
                if result["action"] == "created":
                    stats["lessons_created"] += 1
                elif result["action"] == "updated":
                    stats["lessons_updated"] += 1
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
