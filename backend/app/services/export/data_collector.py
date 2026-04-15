"""
Сервис сбора данных для экспорта журнала.
"""

import logging
from collections import defaultdict
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.group import Group
from app.models.lesson_grade import LessonGrade
from app.models.user import User
from app.schemas.export import (
    AttendanceExportRow,
    GradeExportRow,
    JournalExportData,
    JournalExportMeta,
    LessonExportColumn,
)
from app.services.export.attendance_helpers import (
    build_lesson_export_columns,
    collect_attendance_rows,
    filter_lessons_for_subgroup,
    filter_students_for_export,
    load_export_lessons,
    resolve_export_subgroup,
)
from app.services.reports.base_helpers import get_group, get_group_students

logger = logging.getLogger(__name__)


class ExportDataCollector:
    """Сервис сбора данных для экспорта журнала."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def collect_lessons(
        self, group_id: UUID, start_date: date, end_date: date, subgroup: int | None = None
    ) -> list[LessonExportColumn]:
        """
        Получить занятия группы за период.

        Args:
            group_id: ID группы
            start_date: Начало периода
            end_date: Конец периода

        Returns:
            Список занятий для экспорта
        """
        logger.debug("Сбор занятий для группы %s за период %s - %s", group_id, start_date, end_date)
        lessons = await load_export_lessons(
            self.db,
            group_id=group_id,
            start_date=start_date,
            end_date=end_date,
            subgroup=subgroup,
        )
        logger.info("Найдено %d занятий для экспорта", len(lessons))
        return build_lesson_export_columns(lessons)

    async def collect_grades(self, lesson_ids: list[UUID], students: list[User]) -> list[GradeExportRow]:
        """
        Собрать данные оценок.

        Args:
            lesson_ids: Список ID занятий
            students: Список студентов

        Returns:
            Список строк оценок для экспорта
        """
        if not lesson_ids or not students:
            logger.debug("Нет занятий или студентов для сбора оценок")
            return []

        logger.debug("Сбор оценок для %d занятий и %d студентов", len(lesson_ids), len(students))

        # Получаем все оценки с загрузкой связанных занятий
        query = (
            select(LessonGrade)
            .options(selectinload(LessonGrade.lesson))
            .where(
                LessonGrade.lesson_id.in_(lesson_ids), LessonGrade.student_id.in_([student.id for student in students])
            )
        )

        result = await self.db.execute(query)
        grade_records = list(result.scalars().all())

        # Группируем по студентам
        grades_by_student: dict[UUID, list[LessonGrade]] = defaultdict(list)
        for record in grade_records:
            grades_by_student[record.student_id].append(record)

        rows = []
        for student in students:
            student_grades = grades_by_student.get(student.id, [])

            # Формируем grades_by_work
            grades_by_work: dict[str, int | None] = {}
            total_grade = 0
            grades_count = 0

            for record in student_grades:
                if record.lesson:
                    # Ключ: "{date}_{lesson_number}_{work_number or 0}"
                    work_num = record.work_number if record.work_number else 0
                    key = f"{record.lesson.date}_{record.lesson.lesson_number}_{work_num}"
                    grades_by_work[key] = record.grade

                    total_grade += record.grade
                    grades_count += 1

            # Расчёт среднего балла
            average_grade = round(total_grade / grades_count, 2) if grades_count > 0 else None

            rows.append(
                GradeExportRow(
                    student_id=student.id,
                    student_name=student.full_name,
                    subgroup=student.subgroup,
                    grades_by_work=grades_by_work,
                    average_grade=average_grade,
                    grades_count=grades_count,
                )
            )

        logger.info("Собрано %d строк оценок", len(rows))
        return rows

    async def collect_students(
        self,
        group_id: UUID,
        subgroup: int | None = None,
        student_id: UUID | None = None,
    ) -> list[User]:
        """
        Получить студентов группы.

        Args:
            group_id: ID группы

        Returns:
            Список студентов
        """
        logger.debug("Получение студентов группы %s", group_id)
        students = filter_students_for_export(
            await get_group_students(self.db, group_id),
            subgroup=subgroup,
            student_id=student_id,
        )
        logger.info("Найдено %d студентов", len(students))
        return students

    async def collect_group_info(self, group_id: UUID) -> Group | None:
        """
        Получить информацию о группе.

        Args:
            group_id: ID группы

        Returns:
            Информация о группе или None
        """
        logger.debug("Получение информации о группе %s", group_id)
        return await get_group(self.db, group_id)

    async def collect_all(
        self,
        group_id: UUID,
        start_date: date,
        end_date: date,
        subgroup: int | None = None,
        student_id: UUID | None = None,
        include_attendance: bool = True,
        include_grades: bool = True,
    ) -> JournalExportData:
        """
        Собрать все данные для экспорта.

        Args:
            group_id: ID группы
            start_date: Начало периода
            end_date: Конец периода
            include_attendance: Включить посещаемость
            include_grades: Включить оценки

        Returns:
            Полные данные журнала для экспорта
        """
        logger.info(
            "Начало сбора данных для экспорта: группа=%s, subgroup=%s, student=%s, период=%s - %s",
            group_id,
            subgroup,
            student_id,
            start_date,
            end_date,
        )

        # Получаем базовые данные
        group = await self.collect_group_info(group_id)
        if not group:
            logger.error("Группа %s не найдена", group_id)
            raise ValueError(f"Группа {group_id} не найдена")

        students = await self.collect_students(group_id, subgroup, student_id)
        effective_subgroup = resolve_export_subgroup(
            students,
            subgroup=subgroup,
            student_id=student_id,
        )
        lesson_models = await load_export_lessons(
            self.db,
            group_id=group_id,
            start_date=start_date,
            end_date=end_date,
            subgroup=effective_subgroup,
        )
        lesson_models = filter_lessons_for_subgroup(lesson_models, effective_subgroup)
        lessons = build_lesson_export_columns(lesson_models)

        # Извлекаем ID занятий
        lesson_ids = [lesson.lesson_id for lesson in lessons]

        # Собираем посещаемость и оценки
        attendance_rows: list[AttendanceExportRow] = []
        grade_rows: list[GradeExportRow] = []

        if include_attendance:
            attendance_rows = await collect_attendance_rows(
                self.db,
                group_id=group_id,
                lessons=lesson_models,
                students=students,
            )

        if include_grades:
            grade_rows = await self.collect_grades(lesson_ids, students)

        # Формируем метаданные
        meta = JournalExportMeta(
            group_code=group.code,
            group_name=group.name,
            period_start=start_date,
            period_end=end_date,
            generated_at=datetime.now(UTC),
            total_students=len(students),
            total_lessons=len(lessons),
        )

        logger.info(
            "Сбор данных завершён: %d студентов, %d занятий, %d строк посещаемости, %d строк оценок",
            len(students),
            len(lessons),
            len(attendance_rows),
            len(grade_rows),
        )

        return JournalExportData(
            meta=meta,
            lessons=lessons,
            attendance_rows=attendance_rows,
            grade_rows=grade_rows,
        )
