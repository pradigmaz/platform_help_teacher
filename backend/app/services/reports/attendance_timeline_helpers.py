"""
Timeline-oriented attendance helpers for reports.
"""

from datetime import date
from typing import TypeAlias
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.report import LessonHistoryItem, TodayLessonAttendance
from app.services.attendance_contract import calculate_lesson_attendance_rate
from app.services.schedule_constants import today_msk

AttendanceByLessonMap: TypeAlias = dict[tuple[int | None, UUID], Attendance]
AttendanceByDateLessonMap: TypeAlias = dict[tuple[date, int | None, UUID], Attendance]


def _status_key(status_value: object) -> str:
    return status_value.value.lower() if hasattr(status_value, "value") else str(status_value).lower()


async def get_today_lessons_attendance(
    db: AsyncSession,
    group_id: UUID,
    students: list[User],
    show_names: bool = True,
    target_date: date | None = None,
    period_start_date: date | None = None,
    period_end_date: date | None = None,
) -> list[TodayLessonAttendance]:
    """Получить посещаемость по парам на указанную дату (по умолчанию сегодня)."""
    check_date = target_date or today_msk()
    if period_start_date is not None and check_date < period_start_date:
        return []
    if period_end_date is not None and check_date > period_end_date:
        return []
    student_ids = [student.id for student in students]

    lessons_query = (
        select(Lesson)
        .where(Lesson.group_id == group_id, Lesson.date == check_date, Lesson.is_cancelled.is_(False))
        .order_by(Lesson.lesson_number)
    )
    lessons_result = await db.execute(lessons_query)
    lessons = lessons_result.scalars().all()

    if not lessons:
        return []

    attendance_query = select(Attendance).where(
        Attendance.group_id == group_id,
        Attendance.date == check_date,
        Attendance.student_id.in_(student_ids),
    )
    attendance_result = await db.execute(attendance_query)
    attendance_records = attendance_result.scalars().all()

    attendance_by_lesson: AttendanceByLessonMap = {}
    for attendance in attendance_records:
        attendance_by_lesson[(attendance.lesson_number, attendance.student_id)] = attendance

    result: list[TodayLessonAttendance] = []
    for lesson in lessons:
        relevant_students = (
            students
            if lesson.subgroup is None
            else [student for student in students if student.subgroup == lesson.subgroup]
        )

        present: list[str] = []
        absent: list[str] = []
        late: list[str] = []
        excused: list[str] = []

        for student in relevant_students:
            identifier = student.full_name if show_names else str(student.id)
            attendance_entry: Attendance | None = attendance_by_lesson.get((lesson.lesson_number, student.id))
            if attendance_entry is None:
                absent.append(identifier)
                continue

            status = _status_key(attendance_entry.status)
            if status == "present":
                present.append(identifier)
            elif status == "late":
                late.append(identifier)
            elif status == "excused":
                excused.append(identifier)
            else:
                absent.append(identifier)

        lesson_type_str = lesson.lesson_type.value if hasattr(lesson.lesson_type, "value") else str(lesson.lesson_type)
        result.append(
            TodayLessonAttendance(
                date=lesson.date,
                lesson_number=lesson.lesson_number,
                lesson_type=lesson_type_str,
                topic=lesson.topic,
                subgroup=lesson.subgroup,
                present=present,
                absent=absent,
                late=late,
                excused=excused,
            )
        )

    return result


async def get_recent_lessons_history(
    db: AsyncSession,
    group_id: UUID,
    students: list[User],
    limit: int = 10,
    period_start_date: date | None = None,
    period_end_date: date | None = None,
) -> list[LessonHistoryItem]:
    """Получить историю последних занятий с посещаемостью."""
    check_date = today_msk()
    if period_end_date is not None:
        check_date = min(check_date, period_end_date)
    student_ids = [student.id for student in students]

    lessons_query = (
        select(Lesson)
        .where(Lesson.group_id == group_id, Lesson.date <= check_date, Lesson.is_cancelled.is_(False))
        .order_by(Lesson.date.desc(), Lesson.lesson_number.desc())
        .limit(limit * 2)
    )
    if period_start_date is not None:
        lessons_query = lessons_query.where(Lesson.date >= period_start_date)

    lessons_result = await db.execute(lessons_query)
    lessons = lessons_result.scalars().all()
    if not lessons:
        return []

    lesson_dates = list({lesson.date for lesson in lessons})
    attendance_query = select(Attendance).where(
        Attendance.group_id == group_id,
        Attendance.date.in_(lesson_dates),
        Attendance.student_id.in_(student_ids),
    )
    attendance_result = await db.execute(attendance_query)
    attendance_records = attendance_result.scalars().all()

    attendance_by_date_lesson: AttendanceByDateLessonMap = {}
    for attendance in attendance_records:
        attendance_by_date_lesson[(attendance.date, attendance.lesson_number, attendance.student_id)] = attendance

    result: list[LessonHistoryItem] = []
    for lesson in lessons[:limit]:
        relevant_students = (
            students
            if lesson.subgroup is None
            else [student for student in students if student.subgroup == lesson.subgroup]
        )
        present_count = 0
        total_count = len(relevant_students)

        for student in relevant_students:
            attendance_entry: Attendance | None = attendance_by_date_lesson.get(
                (lesson.date, lesson.lesson_number, student.id)
            )
            if attendance_entry is not None and _status_key(attendance_entry.status) in {"present", "late"}:
                present_count += 1

        attendance_rate = calculate_lesson_attendance_rate(
            present_count=present_count,
            late_count=0,
            total_count=total_count,
        )
        lesson_type_str = lesson.lesson_type.value if hasattr(lesson.lesson_type, "value") else str(lesson.lesson_type)
        result.append(
            LessonHistoryItem(
                date=lesson.date,
                lesson_number=lesson.lesson_number,
                lesson_type=lesson_type_str,
                topic=lesson.topic,
                subgroup=lesson.subgroup,
                attendance_rate=attendance_rate,
                present_count=present_count,
                total_count=total_count,
            )
        )

    return result
