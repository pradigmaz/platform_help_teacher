"""Aggregate admin journal view endpoint."""

from collections import defaultdict
from datetime import date, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_teacher, get_db
from app.models import Attendance, Group, Lesson, LessonGrade, Subject, User, UserRole
from app.models.attendance import AttendanceStatus
from app.models.attestation_settings import AttestationType
from app.schemas.attestation import AttestationResultResponse, AttestationSubjectOption
from app.schemas.group import GroupResponse, StudentInGroupResponse
from app.schemas.journal import (
    JournalLessonResponse,
    JournalResolvedFilters,
    JournalStatsResponse,
    JournalViewResponse,
)
from app.services.attestation_service import AttestationService

router = APIRouter()


def _semester_range(academic_year: int, semester: int, semester_start_date: date | None) -> tuple[date, date]:
    if semester_start_date is not None:
        end = semester_start_date + timedelta(weeks=14)
        return semester_start_date, end
    if semester == 1:
        return date(academic_year, 9, 1), date(academic_year, 12, 31)
    return date(academic_year + 1, 1, 1), date(academic_year + 1, 5, 31)


def _week_bounds(value: date) -> tuple[date, date]:
    week_start = value - timedelta(days=value.weekday())
    return week_start, week_start + timedelta(days=5)


def _attestation_range(period: AttestationType, semester_start: date) -> tuple[date, date]:
    weeks = 8 if period == AttestationType.FIRST else 14
    return semester_start, semester_start + timedelta(weeks=weeks)


def _lesson_type_value(lesson: Lesson) -> str:
    if hasattr(lesson.lesson_type, "value"):
        return lesson.lesson_type.value
    return str(lesson.lesson_type)


def _stats_from_payload(
    lessons: list[Lesson], grade_rows: list[LessonGrade], attendance_rows: list[Attendance]
) -> JournalStatsResponse:
    lectures = sum(1 for lesson in lessons if _lesson_type_value(lesson).lower() == "lecture")
    labs = sum(1 for lesson in lessons if _lesson_type_value(lesson).lower() == "lab")
    practices = sum(1 for lesson in lessons if _lesson_type_value(lesson).lower() == "practice")

    by_status = {
        "present": 0,
        "late": 0,
        "excused": 0,
        "absent": 0,
    }
    for row in attendance_rows:
        status = row.status
        if status == AttendanceStatus.PRESENT:
            by_status["present"] += 1
        elif status == AttendanceStatus.LATE:
            by_status["late"] += 1
        elif status == AttendanceStatus.EXCUSED:
            by_status["excused"] += 1
        elif status == AttendanceStatus.ABSENT:
            by_status["absent"] += 1

    total_attendance = sum(by_status.values())
    present_count = by_status["present"] + by_status["late"]
    attendance_rate = round(present_count / total_attendance * 100, 1) if total_attendance else None

    average_grade = None
    if grade_rows:
        average_grade = round(sum(float(row.grade) for row in grade_rows) / len(grade_rows), 2)

    return JournalStatsResponse(
        total_lessons=len(lessons),
        lectures=lectures,
        labs=labs,
        practices=practices,
        attendance_rate=attendance_rate,
        average_grade=average_grade,
        by_status=by_status,
    )


@router.get("/view", response_model=JournalViewResponse)
async def get_journal_view(
    group_id: UUID | None = Query(default=None),
    subject_id: UUID | None = Query(default=None),
    lesson_type: str | None = Query(default=None),
    week_start: date = Query(...),
    week_end: date = Query(...),
    attestation_period: str = Query(default="all", pattern="^(all|first|second)$"),
    academic_year: int = Query(..., ge=2020, le=2100),
    semester: int = Query(..., ge=1, le=2),
    semester_start_date: date | None = Query(default=None),
    lesson_id: UUID | None = Query(default=None),
    include_attestation_scores: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
) -> JournalViewResponse:
    groups_result = await db.execute(
        select(Group, func.count(User.id).label("students_count"))
        .outerjoin(User, User.group_id == Group.id)
        .where(Group.is_archived.is_(False))
        .group_by(Group.id)
        .order_by(Group.name.asc())
    )
    groups: list[GroupResponse] = []
    for group, students_count in groups_result:
        payload = GroupResponse.model_validate(group)
        payload.students_count = students_count
        groups.append(payload)

    selected_lesson: Lesson | None = None
    if lesson_id is not None:
        lesson_result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
        selected_lesson = lesson_result.scalar_one_or_none()

    resolved_group_id = group_id or (selected_lesson.group_id if selected_lesson else None)
    if resolved_group_id is None and groups:
        resolved_group_id = groups[0].id

    resolved_subject_id = subject_id or (selected_lesson.subject_id if selected_lesson else None)
    resolved_week_start = week_start
    resolved_week_end = week_end
    if selected_lesson is not None and attestation_period == "all":
        resolved_week_start, resolved_week_end = _week_bounds(selected_lesson.date)

    if resolved_group_id is None:
        return JournalViewResponse(
            resolved=JournalResolvedFilters(
                group_id=None,
                subject_id=None,
                week_start=resolved_week_start,
                week_end=resolved_week_end,
            ),
            groups=groups,
            subjects=[],
            lessons=[],
            students=[],
            attendance={},
            grades={},
            attestation_scores={},
            stats=None,
        )

    semester_start, semester_end = _semester_range(academic_year, semester, semester_start_date)
    if attestation_period == "all":
        range_start = max(resolved_week_start, semester_start)
        range_end = min(resolved_week_end, semester_end)
    else:
        period_type = AttestationType(attestation_period)
        range_start, range_end = _attestation_range(period_type, semester_start)

    group_result = await db.execute(
        select(Group).options(selectinload(Group.users)).where(Group.id == resolved_group_id)
    )
    group = group_result.scalar_one_or_none()
    students = []
    if group is not None:
        active_students = sorted((user for user in group.users if user.is_active), key=lambda row: row.full_name or "")
        students = [StudentInGroupResponse.model_validate(student) for student in active_students]

    semester_subject_ids_result = await db.execute(
        select(Lesson.subject_id)
        .where(Lesson.group_id == resolved_group_id)
        .where(Lesson.subject_id.isnot(None))
        .where(Lesson.date >= semester_start)
        .where(Lesson.date <= semester_end)
        .distinct()
    )
    semester_subject_ids = [value for value in semester_subject_ids_result.scalars().all() if value is not None]
    subjects: list[AttestationSubjectOption] = []
    if semester_subject_ids:
        subjects_result = await db.execute(
            select(Subject).where(Subject.id.in_(semester_subject_ids)).order_by(Subject.name.asc())
        )
        subjects = [
            AttestationSubjectOption(id=subject.id, name=subject.name, code=subject.code)
            for subject in subjects_result.scalars().all()
        ]
    subject_ids_set = {subject.id for subject in subjects}
    if resolved_subject_id is not None and resolved_subject_id not in subject_ids_set:
        resolved_subject_id = None

    lessons_query = (
        select(Lesson)
        .options(selectinload(Lesson.subject), selectinload(Lesson.group))
        .where(Lesson.group_id == resolved_group_id)
        .where(Lesson.date >= range_start)
        .where(Lesson.date <= range_end)
        .order_by(Lesson.date.asc(), Lesson.lesson_number.asc())
    )
    if resolved_subject_id is not None:
        lessons_query = lessons_query.where(Lesson.subject_id == resolved_subject_id)
    if lesson_type and lesson_type != "all":
        lessons_query = lessons_query.where(Lesson.lesson_type == lesson_type)

    lessons_result = await db.execute(lessons_query)
    lessons = list(lessons_result.scalars().all())
    lesson_ids = [lesson.id for lesson in lessons]

    attendance_rows: list[Attendance] = []
    grades_rows: list[LessonGrade] = []
    attendance_payload: dict[str, dict[str, str]] = {}
    grades_payload: dict[str, dict[str, dict[str, int | bool | None]]] = {}
    if lesson_ids:
        attendance_result = await db.execute(
            select(Attendance)
            .where(and_(Attendance.group_id == resolved_group_id, Attendance.lesson_id.in_(lesson_ids)))
            .options(selectinload(Attendance.student))
        )
        attendance_rows = list(attendance_result.scalars().all())
        attendance_payload = defaultdict(dict)
        for row in attendance_rows:
            if row.lesson_id is None:
                continue
            attendance_payload[str(row.lesson_id)][str(row.student_id)] = row.status.value

        grades_result = await db.execute(
            select(LessonGrade).where(LessonGrade.lesson_id.in_(lesson_ids)).options(selectinload(LessonGrade.student))
        )
        grades_rows = list(grades_result.scalars().all())
        grouped_grades: dict[tuple[str, str], list[LessonGrade]] = defaultdict(list)
        for row in grades_rows:
            grouped_grades[(str(row.lesson_id), str(row.student_id))].append(row)

        grades_payload = defaultdict(dict)
        for (lesson_key, student_key), rows in grouped_grades.items():
            first = rows[0]
            has_conflict = len(rows) > 1
            grades_payload[lesson_key][student_key] = {
                "grade": None if has_conflict else first.grade,
                "work_number": None if has_conflict else first.work_number,
                "has_conflict": has_conflict,
                "conflict_count": len(rows),
            }

    attestation_scores: dict[str, AttestationResultResponse] = {}
    if include_attestation_scores and resolved_subject_id is not None:
        service = AttestationService(db)
        results, _ = await service.calculate_group_scores_batch(
            group_id=resolved_group_id,
            attestation_type=AttestationType(attestation_period),
            students=[group_user for group_user in (group.users if group else []) if group_user.is_active],
            subject_id=resolved_subject_id,
        )
        attestation_scores = {
            str(result.student_id): AttestationResultResponse(**result.model_dump()) for result in results
        }

    return JournalViewResponse(
        resolved=JournalResolvedFilters(
            group_id=resolved_group_id,
            subject_id=resolved_subject_id,
            week_start=range_start if attestation_period != "all" else resolved_week_start,
            week_end=range_end if attestation_period != "all" else resolved_week_end,
        ),
        groups=groups,
        subjects=subjects,
        lessons=[
            JournalLessonResponse(
                id=lesson.id,
                date=lesson.date,
                lesson_number=lesson.lesson_number,
                lesson_type=_lesson_type_value(lesson),
                topic=lesson.topic,
                work_number=lesson.work_number,
                lecture_work_type=lesson.lecture_work_type,
                subgroup=lesson.subgroup,
                is_cancelled=lesson.is_cancelled,
                subject_id=lesson.subject_id,
                subject_name=lesson.subject.name if lesson.subject else None,
                group_id=lesson.group_id,
                group_name=lesson.group.name if lesson.group else None,
            )
            for lesson in lessons
        ],
        students=students,
        attendance=dict(attendance_payload),
        grades=dict(grades_payload),
        attestation_scores=attestation_scores,
        stats=_stats_from_payload(lessons, grades_rows, attendance_rows),
    )
