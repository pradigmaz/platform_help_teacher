"""
Сервис сбора данных для экспорта журнала.
"""
import logging
from datetime import date, datetime, timezone
from typing import List, Dict, Optional
from uuid import UUID
from collections import defaultdict

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lesson import Lesson
from app.models.attendance import Attendance, AttendanceStatus
from app.models.lesson_grade import LessonGrade
from app.models.user import User
from app.models.group import Group
from app.schemas.export import (
    LessonExportColumn,
    AttendanceExportRow,
    GradeExportRow,
    JournalExportMeta,
    JournalExportData,
)
from app.services.reports.base_helpers import get_group_students, get_group

logger = logging.getLogger(__name__)


class ExportDataCollector:
    """Сервис сбора данных для экспорта журнала."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def collect_lessons(
        self, group_id: UUID, start_date: date, end_date: date
    ) -> List[LessonExportColumn]:
        """
        Получить занятия группы за период.

        Args:
            group_id: ID группы
            start_date: Начало периода
            end_date: Конец периода

        Returns:
            Список занятий для экспорта
        """
        logger.debug(
            "Сбор занятий для группы %s за период %s - %s",
            group_id, start_date, end_date
        )

        query = (
            select(Lesson)
            .where(
                and_(
                    Lesson.group_id == group_id,
                    Lesson.date >= start_date,
                    Lesson.date <= end_date,
                    Lesson.is_cancelled == False,
                )
            )
            .order_by(Lesson.date, Lesson.lesson_number)
        )

        result = await self.db.execute(query)
        lessons = list(result.scalars().all())

        logger.info("Найдено %d занятий для экспорта", len(lessons))

        return [
            LessonExportColumn(
                lesson_id=lesson.id,
                date=lesson.date,
                lesson_number=lesson.lesson_number,
                lesson_type=lesson.lesson_type.value,
                topic=lesson.topic,
                work_number=lesson.work_number,
                subgroup=lesson.subgroup,
            )
            for lesson in lessons
        ]

    async def collect_attendance(
        self, group_id: UUID, lesson_ids: List[UUID], students: List[User]
    ) -> List[AttendanceExportRow]:
        """
        Собрать данные посещаемости.

        Args:
            group_id: ID группы
            lesson_ids: Список ID занятий
            students: Список студентов

        Returns:
            Список строк посещаемости для экспорта
        """
        if not lesson_ids or not students:
            logger.debug("Нет занятий или студентов для сбора посещаемости")
            return []

        logger.debug(
            "Сбор посещаемости для %d занятий и %d студентов",
            len(lesson_ids), len(students)
        )

        # Получаем все записи посещаемости
        query = (
            select(Attendance)
            .options(selectinload(Attendance.lesson))
            .where(
                and_(
                    Attendance.group_id == group_id,
                    Attendance.lesson_id.in_(lesson_ids),
                )
            )
        )

        result = await self.db.execute(query)
        attendance_records = list(result.scalars().all())

        # Группируем по студентам
        attendance_by_student: Dict[UUID, List[Attendance]] = defaultdict(list)
        for record in attendance_records:
            attendance_by_student[record.student_id].append(record)

        rows = []
        for student in students:
            student_attendance = attendance_by_student.get(student.id, [])

            # Формируем attendance_by_date
            attendance_by_date: Dict[str, str] = {}
            stats = {
                "present_count": 0,
                "absent_count": 0,
                "late_count": 0,
                "excused_count": 0,
                "total": 0,
            }

            for record in student_attendance:
                # Ключ: "{date}_{lesson_number}"
                key = f"{record.date}_{record.lesson_number}"
                attendance_by_date[key] = record.status.value

                # Обновляем статистику
                stats["total"] += 1
                if record.status == AttendanceStatus.PRESENT:
                    stats["present_count"] += 1
                elif record.status == AttendanceStatus.ABSENT:
                    stats["absent_count"] += 1
                elif record.status == AttendanceStatus.LATE:
                    stats["late_count"] += 1
                elif record.status == AttendanceStatus.EXCUSED:
                    stats["excused_count"] += 1

            # Расчёт attendance_rate
            if stats["total"] > 0:
                attendance_rate = (
                    (
                        stats["present_count"]
                        + stats["late_count"] * 0.5
                        + stats["excused_count"] * 0.5
                    )
                    / stats["total"]
                    * 100
                )
            else:
                attendance_rate = 0.0

            rows.append(
                AttendanceExportRow(
                    student_id=student.id,
                    student_name=student.full_name,
                    subgroup=student.subgroup,
                    attendance_by_date=attendance_by_date,
                    stats=stats,
                    attendance_rate=round(attendance_rate, 2),
                )
            )

        logger.info("Собрано %d строк посещаемости", len(rows))
        return rows

    async def collect_grades(
        self, lesson_ids: List[UUID], students: List[User]
    ) -> List[GradeExportRow]:
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

        logger.debug(
            "Сбор оценок для %d занятий и %d студентов",
            len(lesson_ids), len(students)
        )

        # Получаем все оценки с загрузкой связанных занятий
        query = (
            select(LessonGrade)
            .options(selectinload(LessonGrade.lesson))
            .where(LessonGrade.lesson_id.in_(lesson_ids))
        )

        result = await self.db.execute(query)
        grade_records = list(result.scalars().all())

        # Группируем по студентам
        grades_by_student: Dict[UUID, List[LessonGrade]] = defaultdict(list)
        for record in grade_records:
            grades_by_student[record.student_id].append(record)

        rows = []
        for student in students:
            student_grades = grades_by_student.get(student.id, [])

            # Формируем grades_by_work
            grades_by_work: Dict[str, Optional[int]] = {}
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
            average_grade = (
                round(total_grade / grades_count, 2) if grades_count > 0 else None
            )

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

    async def collect_students(self, group_id: UUID) -> List[User]:
        """
        Получить студентов группы.

        Args:
            group_id: ID группы

        Returns:
            Список студентов
        """
        logger.debug("Получение студентов группы %s", group_id)
        students = await get_group_students(self.db, group_id)
        logger.info("Найдено %d студентов", len(students))
        return students

    async def collect_group_info(self, group_id: UUID) -> Optional[Group]:
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
            "Начало сбора данных для экспорта: группа=%s, период=%s - %s",
            group_id, start_date, end_date
        )

        # Получаем базовые данные
        group = await self.collect_group_info(group_id)
        if not group:
            logger.error("Группа %s не найдена", group_id)
            raise ValueError(f"Группа {group_id} не найдена")

        students = await self.collect_students(group_id)
        lessons = await self.collect_lessons(group_id, start_date, end_date)

        # Извлекаем ID занятий
        lesson_ids = [lesson.lesson_id for lesson in lessons]

        # Собираем посещаемость и оценки
        attendance_rows: List[AttendanceExportRow] = []
        grade_rows: List[GradeExportRow] = []

        if include_attendance:
            attendance_rows = await self.collect_attendance(
                group_id, lesson_ids, students
            )

        if include_grades:
            grade_rows = await self.collect_grades(lesson_ids, students)

        # Формируем метаданные
        meta = JournalExportMeta(
            group_code=group.code,
            group_name=group.name,
            period_start=start_date,
            period_end=end_date,
            generated_at=datetime.now(timezone.utc),
            total_students=len(students),
            total_lessons=len(lessons),
        )

        logger.info(
            "Сбор данных завершён: %d студентов, %d занятий, "
            "%d строк посещаемости, %d строк оценок",
            len(students), len(lessons), len(attendance_rows), len(grade_rows)
        )

        return JournalExportData(
            meta=meta,
            lessons=lessons,
            attendance_rows=attendance_rows,
            grade_rows=grade_rows,
        )
