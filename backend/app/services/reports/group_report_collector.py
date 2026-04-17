"""Internal collector for public group report data."""

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.group_report import GroupReport, ReportType
from app.models.lesson import Lesson
from app.schemas.report import PublicReportData
from app.services.attendance_contract import StudentAttendanceSnapshot
from app.services.attestation.service import AttestationService

from .attendance_helpers import (
    build_attendance_distribution,
    build_full_attendance_stats,
    build_group_attendance_stats,
    get_recent_lessons_history,
    get_today_lessons_attendance,
    load_group_attendance_snapshots,
)
from .base_helpers import get_filtered_teacher_contacts, get_group, get_group_students, get_user
from .labs_helpers import calculate_grade_distribution
from .notes_helpers import get_students_notes
from .report_builder import build_empty_report
from .report_lab_service import get_group_labs_stats, get_lab_progress
from .report_subject_helpers import resolve_report_subject_context
from .semester_helpers import get_semester_info, get_semester_start_date
from .student_builder import process_students

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AttendanceSection:
    lessons: list[Lesson]
    snapshots: dict[UUID, StudentAttendanceSnapshot]
    student_stats: dict[UUID, Any]
    distribution: Any | None = None
    stats: Any | None = None
    today_lessons: Any | None = None
    lesson_history: Any | None = None


def _resolve_attestation_type(attestation_type: str) -> AttestationType:
    return AttestationType.SECOND if attestation_type == "second" else AttestationType.FIRST


def _serialize_grade_scale(att_type: AttestationType) -> dict[str, list[float]]:
    grade_scale = AttestationSettings.get_grade_scale(att_type)
    return {key: [float(value) for value in values] for key, values in grade_scale.items()}


async def _load_attestation_context(
    db: AsyncSession,
    group_id: UUID,
    students: list[Any],
    att_type: AttestationType,
    subject_id: UUID | None = None,
) -> tuple[AttestationSettings, list[Any], dict[UUID, Any]]:
    attestation_service = AttestationService(db)
    settings = await attestation_service.get_or_create_settings(att_type)
    try:
        attestation_results, _ = await attestation_service.calculate_group_scores_batch(
            group_id=group_id,
            attestation_type=att_type,
            students=students,
            subject_id=subject_id,
        )
    except ValueError as exc:
        logger.warning("Report attestation skipped for group %s: %s", group_id, exc)
        attestation_results = []

    return settings, attestation_results, {result.student_id: result for result in attestation_results}


async def _load_attendance_section(
    db: AsyncSession,
    report: GroupReport,
    group_id: UUID,
    students: list[Any],
    *,
    period_start,
    period_end,
    has_subgroups: bool,
    subject_id: UUID | None,
) -> AttendanceSection:
    if not report.show_attendance:
        return AttendanceSection(lessons=[], snapshots={}, student_stats={})

    lessons, snapshots = await load_group_attendance_snapshots(
        db,
        group_id,
        students,
        period_start=period_start,
        period_end=period_end,
        subject_id=subject_id,
    )
    student_stats = build_group_attendance_stats(students, snapshots)
    lesson_history = await get_recent_lessons_history(
        db,
        group_id,
        students,
        limit=10,
        period_start_date=period_start,
        period_end_date=period_end,
        subject_id=subject_id,
    )
    stats = build_full_attendance_stats(
        lessons=lessons,
        students=students,
        snapshots=snapshots,
        has_subgroups=has_subgroups,
    )
    today_lessons = await get_today_lessons_attendance(
        db,
        group_id,
        students,
        show_names=report.show_names,
        period_start_date=period_start,
        period_end_date=period_end,
        subject_id=subject_id,
    )
    return AttendanceSection(
        lessons=lessons,
        snapshots=snapshots,
        student_stats=student_stats,
        distribution=build_attendance_distribution(snapshots),
        stats=stats,
        today_lessons=today_lessons,
        lesson_history=lesson_history,
    )


async def _load_notes_map(db: AsyncSession, report: GroupReport, students: list[Any]) -> dict[UUID, list[str]]:
    if not report.show_notes:
        return {}
    return await get_students_notes(db, [student.id for student in students], visible_only=True)


def _sort_students_data(students_data: list[Any], report: GroupReport) -> None:
    if report.show_rating and report.show_grades:
        students_data.sort(key=lambda student: student.total_score or 0, reverse=True)
        return
    students_data.sort(key=lambda student: student.name or "")


async def collect_group_report_data(
    db: AsyncSession,
    report: GroupReport,
    attestation_type: str = "first",
    subject_id: UUID | None = None,
) -> PublicReportData:
    """Collect public group report data without exposing orchestration in the facade."""
    att_type = _resolve_attestation_type(attestation_type)

    group = await get_group(db, report.group_id)
    teacher = await get_user(db, report.created_by)
    students = await get_group_students(db, report.group_id)
    is_early, max_points, min_passing, is_second_available = await get_semester_info(db, att_type)
    semester_start = await get_semester_start_date(db)
    grade_scale_json = _serialize_grade_scale(att_type)

    if not students:
        return build_empty_report(
            report,
            group,
            teacher,
            attestation_type,
            max_points,
            min_passing,
            is_second_available,
        )

    settings = await AttestationService(db).get_or_create_settings(att_type)
    has_subgroups = bool(group and hasattr(group, "has_subgroups") and group.has_subgroups)
    period_start, period_end = settings.get_effective_period()
    subject_context = await resolve_report_subject_context(
        db,
        group_id=report.group_id,
        settings=settings,
        requested_subject_id=subject_id,
    )
    effective_subject_id = subject_context.selected_subject_id
    subject_ready = not subject_context.requires_subject or effective_subject_id is not None

    if subject_ready:
        _, attestation_results, results_map = await _load_attestation_context(
            db,
            report.group_id,
            students,
            att_type,
            effective_subject_id,
        )
        attendance_section = await _load_attendance_section(
            db,
            report,
            report.group_id,
            students,
            period_start=period_start,
            period_end=period_end,
            has_subgroups=has_subgroups,
            subject_id=effective_subject_id,
        )
        labs_data = await get_group_labs_stats(
            db,
            report.group_id,
            students,
            settings,
            results_map,
            subject_id=effective_subject_id,
        )
        students_data, passing_count, failing_count, total_score_sum = process_students(
            students,
            results_map,
            attendance_section.student_stats,
            labs_data,
            await _load_notes_map(db, report, students),
            report,
        )
        _sort_students_data(students_data, report)
    else:
        attestation_results = []
        results_map = {}
        attendance_section = AttendanceSection(lessons=[], snapshots={}, student_stats={})
        labs_data = {}
        students_data = []
        passing_count = 0
        failing_count = 0
        total_score_sum = 0.0

    lab_progress = None
    lab_progress_by_subgroup = None
    grade_distribution = None
    if report.show_grades and subject_ready:
        lab_progress, lab_progress_by_subgroup = await get_lab_progress(
            db,
            report.group_id,
            students,
            settings,
            has_subgroups,
            subject_id=effective_subject_id,
        )
        grade_distribution = calculate_grade_distribution(attestation_results)

    return PublicReportData(
        group_code=group.code if group else "",
        group_name=group.name if group else None,
        subject_name=subject_context.subject_name,
        report_type=ReportType(report.report_type),
        semester_start_date=semester_start,
        teacher_contacts=get_filtered_teacher_contacts(teacher, "report") if teacher else None,
        show_names=report.show_names,
        show_grades=report.show_grades,
        is_early_semester=is_early,
        show_attendance=report.show_attendance,
        show_notes=report.show_notes,
        show_rating=report.show_rating,
        total_students=len(students),
        passing_students=passing_count if report.show_grades and subject_ready else None,
        failing_students=failing_count if report.show_grades and subject_ready else None,
        average_score=round(total_score_sum / len(students), 2)
        if students and report.show_grades and subject_ready
        else None,
        max_points=max_points,
        min_passing_points=min_passing,
        grade_scale=grade_scale_json if report.show_grades else None,
        attestation_type=attestation_type,
        is_second_available=is_second_available,
        requires_subject=subject_context.requires_subject,
        selected_subject_id=effective_subject_id,
        available_subjects=subject_context.available_subjects,
        has_subgroups=has_subgroups,
        students=students_data,
        attendance_distribution=attendance_section.distribution,
        attendance_stats=attendance_section.stats,
        lab_progress=lab_progress,
        lab_progress_by_subgroup=lab_progress_by_subgroup,
        grade_distribution=grade_distribution,
        today_lessons=attendance_section.today_lessons,
        lesson_history=attendance_section.lesson_history,
    )
