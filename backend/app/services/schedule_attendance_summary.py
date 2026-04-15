"""Attendance summary helpers for the admin schedule view."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Attendance, Lesson, User
from app.models.user import UserRole
from app.schemas.schedule import (
    AttendanceSummaryState,
    GroupedLectureAttendanceSummaryResponse,
    LessonAttendanceSummaryResponse,
)
from app.services.schedule_constants import LESSON_TIMES, now_msk

GroupedLectureKey = tuple[str, int, str | None]


@dataclass(frozen=True)
class GroupedLectureSummaryResult:
    summary: GroupedLectureAttendanceSummaryResponse
    is_cancelled: bool
    ended_early: bool


@dataclass(frozen=True)
class ScheduleAttendanceSummaryResult:
    lesson_summaries: dict[UUID, LessonAttendanceSummaryResponse]
    grouped_lecture_summaries: dict[GroupedLectureKey, GroupedLectureSummaryResult]


def grouped_lecture_item_key(item: dict) -> GroupedLectureKey:
    return (item["date"], item["lesson_number"], item["subject_id"])


def is_schedule_slot_past(slot_date: date, lesson_number: int, current_time: datetime | None = None) -> bool:
    now = current_time or now_msk()
    if slot_date < now.date():
        return True
    if slot_date > now.date():
        return False
    lesson_times = LESSON_TIMES.get(lesson_number)
    if lesson_times is None:
        return False
    end_time = time.fromisoformat(lesson_times[1])
    return now.time() > end_time


def _resolve_summary_state(marked_count: int, expected_count: int) -> AttendanceSummaryState:
    if expected_count == 0:
        return "complete"
    if marked_count == 0:
        return "unmarked"
    if marked_count < expected_count:
        return "partial"
    return "complete"


def _relevant_student_ids(students: Iterable[User], subgroup: int | None) -> set[UUID]:
    if subgroup is None:
        return {student.id for student in students}
    return {student.id for student in students if student.subgroup == subgroup}


def calculate_lesson_attendance_summary(
    lesson: Lesson,
    students: Iterable[User],
    marked_student_ids: set[UUID],
    *,
    current_time: datetime | None = None,
) -> LessonAttendanceSummaryResponse:
    is_past = is_schedule_slot_past(lesson.date, lesson.lesson_number, current_time)
    relevant_ids = _relevant_student_ids(students, lesson.subgroup)
    marked_count = len(relevant_ids & marked_student_ids)
    expected_count = len(relevant_ids)

    if not is_past:
        return LessonAttendanceSummaryResponse(
            state="hidden",
            marked_count=marked_count,
            expected_count=expected_count,
            is_past=False,
        )
    if lesson.is_cancelled:
        return LessonAttendanceSummaryResponse(
            state="not_applicable",
            marked_count=0,
            expected_count=0,
            is_past=True,
        )
    return LessonAttendanceSummaryResponse(
        state=_resolve_summary_state(marked_count, expected_count),
        marked_count=marked_count,
        expected_count=expected_count,
        is_past=True,
    )


def calculate_grouped_lecture_attendance_summary(
    lessons: Iterable[Lesson],
    students_by_group: dict[UUID, list[User]],
    marked_by_lesson: dict[UUID, set[UUID]],
    *,
    current_time: datetime | None = None,
) -> GroupedLectureSummaryResult:
    lesson_list = list(lessons)
    if not lesson_list:
        empty_summary = GroupedLectureAttendanceSummaryResponse(
            state="not_applicable",
            marked_count=0,
            expected_count=0,
            is_past=False,
        )
        return GroupedLectureSummaryResult(summary=empty_summary, is_cancelled=True, ended_early=False)

    reference_lesson = lesson_list[0]
    is_past = is_schedule_slot_past(reference_lesson.date, reference_lesson.lesson_number, current_time)
    active_lessons = [lesson for lesson in lesson_list if not lesson.is_cancelled]

    expected_ids: set[UUID] = set()
    marked_ids: set[UUID] = set()
    for lesson in active_lessons:
        relevant_ids = _relevant_student_ids(students_by_group.get(lesson.group_id, []), lesson.subgroup)
        expected_ids.update(relevant_ids)
        marked_ids.update(relevant_ids & marked_by_lesson.get(lesson.id, set()))

    if not is_past:
        summary = GroupedLectureAttendanceSummaryResponse(
            state="hidden",
            marked_count=len(marked_ids),
            expected_count=len(expected_ids),
            is_past=False,
        )
        return GroupedLectureSummaryResult(
            summary=summary,
            is_cancelled=not active_lessons,
            ended_early=any(lesson.ended_early for lesson in active_lessons),
        )

    if not active_lessons:
        summary = GroupedLectureAttendanceSummaryResponse(
            state="not_applicable",
            marked_count=0,
            expected_count=0,
            is_past=True,
        )
        return GroupedLectureSummaryResult(summary=summary, is_cancelled=True, ended_early=False)

    marked_count = len(marked_ids)
    expected_count = len(expected_ids)
    summary = GroupedLectureAttendanceSummaryResponse(
        state=_resolve_summary_state(marked_count, expected_count),
        marked_count=marked_count,
        expected_count=expected_count,
        is_past=True,
    )

    ended_early = any(lesson.ended_early for lesson in active_lessons)
    return GroupedLectureSummaryResult(summary=summary, is_cancelled=False, ended_early=ended_early)


class ScheduleAttendanceSummaryService:
    async def build(
        self,
        db: AsyncSession,
        *,
        regular_lessons: Iterable[Lesson],
        grouped_lecture_items: list[dict],
    ) -> ScheduleAttendanceSummaryResult:
        lesson_rows = list(regular_lessons)
        grouped_lesson_ids = [
            UUID(group["lesson_id"]) for item in grouped_lecture_items for group in item.get("groups", [])
        ]

        lecture_lessons: list[Lesson] = []
        if grouped_lesson_ids:
            lesson_result = await db.execute(select(Lesson).where(Lesson.id.in_(grouped_lesson_ids)))
            lecture_lessons = list(lesson_result.scalars().all())
        lecture_lessons_by_id = {lesson.id: lesson for lesson in lecture_lessons}

        all_lessons = lesson_rows + lecture_lessons
        group_ids = {lesson.group_id for lesson in all_lessons}
        students_by_group: dict[UUID, list[User]] = defaultdict(list)
        if group_ids:
            students_result = await db.execute(
                select(User)
                .where(User.group_id.in_(group_ids), User.role == UserRole.STUDENT, User.is_active)
                .order_by(User.full_name)
            )
            for student in students_result.scalars().all():
                if student.group_id is not None:
                    students_by_group[student.group_id].append(student)

        marked_by_lesson: dict[UUID, set[UUID]] = defaultdict(set)
        lesson_ids = {lesson.id for lesson in all_lessons}
        if lesson_ids:
            attendance_result = await db.execute(
                select(Attendance.lesson_id, Attendance.student_id).where(Attendance.lesson_id.in_(lesson_ids))
            )
            for lesson_id, student_id in attendance_result.all():
                if lesson_id is not None:
                    marked_by_lesson[lesson_id].add(student_id)

        current_time = now_msk()
        lesson_summaries = {
            lesson.id: calculate_lesson_attendance_summary(
                lesson,
                students_by_group.get(lesson.group_id, []),
                marked_by_lesson.get(lesson.id, set()),
                current_time=current_time,
            )
            for lesson in lesson_rows
        }

        grouped_summaries: dict[GroupedLectureKey, GroupedLectureSummaryResult] = {}
        for item in grouped_lecture_items:
            lessons = [
                lecture_lessons_by_id[UUID(group["lesson_id"])]
                for group in item.get("groups", [])
                if UUID(group["lesson_id"]) in lecture_lessons_by_id
            ]
            grouped_summaries[grouped_lecture_item_key(item)] = calculate_grouped_lecture_attendance_summary(
                lessons,
                students_by_group,
                marked_by_lesson,
                current_time=current_time,
            )

        return ScheduleAttendanceSummaryResult(
            lesson_summaries=lesson_summaries,
            grouped_lecture_summaries=grouped_summaries,
        )


schedule_attendance_summary_service = ScheduleAttendanceSummaryService()
