"""Helpers for collecting public student detail report data."""

import logging
from typing import TypedDict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.group_report import GroupReport
from app.schemas.report import StudentDetailData
from app.services.attestation.service import AttestationService

from .activity_helpers import generate_recommendations, get_student_activity
from .attendance_helpers import (
    build_student_attendance_history,
    load_group_attendance_snapshots,
    snapshot_to_stats,
)
from .base_helpers import get_group, get_group_students, get_user
from .report_lab_detail_service import get_student_lab_submissions
from .report_subject_helpers import resolve_report_subject_context
from .semester_helpers import get_semester_info

logger = logging.getLogger(__name__)


class StudentComparisonStats(TypedDict):
    average: float
    rank: int
    total: int


async def collect_student_report_data(
    db: AsyncSession,
    report: GroupReport,
    student_id: UUID,
    attestation_type: str = "first",
    subject_id: UUID | None = None,
) -> StudentDetailData | None:
    """Собрать детальные данные публичного отчёта по студенту."""
    att_type = AttestationType.SECOND if attestation_type == "second" else AttestationType.FIRST

    student = await get_user(db, student_id)
    if not student or student.group_id != report.group_id:
        return None

    group = await get_group(db, report.group_id)
    is_early, _, _, _ = await get_semester_info(db, att_type)

    attestation_service = AttestationService(db)
    settings = await attestation_service.get_or_create_settings(att_type)
    period_start, period_end = settings.get_effective_period()
    subject_context = await resolve_report_subject_context(
        db,
        group_id=report.group_id,
        settings=settings,
        requested_subject_id=subject_id,
    )
    effective_subject_id = subject_context.selected_subject_id
    subject_ready = not subject_context.requires_subject or effective_subject_id is not None
    try:
        result = (
            await attestation_service.calculate_student_score(
                student_id=student_id,
                group_id=report.group_id,
                attestation_type=att_type,
                subject_id=effective_subject_id,
            )
            if subject_ready
            else None
        )
    except Exception as exc:
        logger.error("Error calculating score for student %s: %s", student_id, exc)
        result = None

    attendance_history = None
    att_stats: dict[str, int | float] = {}
    if report.show_attendance and subject_ready:
        attendance_lessons, attendance_snapshots = await load_group_attendance_snapshots(
            db,
            report.group_id,
            [student],
            period_start=period_start,
            period_end=period_end,
            subject_id=effective_subject_id,
        )
        student_snapshot = attendance_snapshots.get(student_id)
        attendance_history = build_student_attendance_history(attendance_lessons, student_snapshot)
        att_stats = snapshot_to_stats(student_snapshot)

    lab_submissions = None
    labs_completed = 0
    labs_total = 0
    if report.show_grades and subject_ready:
        lab_submissions = await get_student_lab_submissions(
            db,
            report.group_id,
            student_id,
            settings,
            effective_subject_id,
        )
        if result is not None:
            labs_completed = result.breakdown.labs_count
            labs_total = result.breakdown.labs_required
        else:
            labs_completed = sum(1 for submission in lab_submissions if submission.is_submitted)
            labs_total = len(lab_submissions)

    activity_records = None
    total_activity_points = 0.0
    if report.show_grades and subject_ready:
        activity_records = await get_student_activity(
            db,
            student_id,
            attestation_type=att_type,
            subject_id=effective_subject_id,
        )
        total_activity_points = sum(activity.points for activity in activity_records)

    group_average = None
    rank_in_group = None
    total_in_group = None
    if report.show_rating and result and subject_ready:
        group_stats = await _get_group_comparison_stats(
            db=db,
            group_id=report.group_id,
            student_id=student_id,
            student_score=result.total_score,
            attestation_type=att_type,
            subject_id=effective_subject_id,
        )
        if group_stats is not None:
            group_average = group_stats["average"]
            rank_in_group = group_stats["rank"]
            total_in_group = group_stats["total"]

    is_passing = result.is_passing if result else False
    recommendations = None
    if not is_passing and subject_ready:
        recommendations = generate_recommendations(result, att_stats, labs_completed, labs_total)

    return StudentDetailData(
        id=student_id,
        name=student.full_name if report.show_names else None,
        group_code=group.code if group else "",
        subject_name=subject_context.subject_name,
        requires_subject=subject_context.requires_subject,
        selected_subject_id=effective_subject_id,
        available_subjects=subject_context.available_subjects,
        total_score=result.total_score if result and report.show_grades else None,
        lab_score=result.breakdown.labs_score if result and report.show_grades else None,
        attendance_score=result.breakdown.attendance_score if result and report.show_grades else None,
        activity_score=result.breakdown.activity_score if result and report.show_grades else None,
        grade=result.grade if result and report.show_grades else None,
        is_passing=is_passing if report.show_grades else None,
        is_early_semester=is_early,
        max_points=result.max_points if result else att_type.max_points,
        min_passing_points=result.min_passing_points
        if result
        else AttestationSettings.get_min_passing_points(att_type),
        group_average_score=group_average,
        rank_in_group=rank_in_group,
        total_in_group=total_in_group,
        attendance_rate=att_stats.get("rate"),
        attendance_history=attendance_history,
        present_count=int(att_stats.get("present", 0)),
        absent_count=int(att_stats.get("absent", 0)),
        late_count=int(att_stats.get("late", 0)),
        excused_count=int(att_stats.get("excused", 0)),
        total_lessons=int(att_stats.get("total", 0)),
        labs_completed=labs_completed if report.show_grades else None,
        labs_total=labs_total if report.show_grades else None,
        lab_submissions=lab_submissions,
        activity_records=activity_records,
        total_activity_points=total_activity_points if report.show_grades else None,
        recommendations=recommendations,
        needs_attention=not is_passing if subject_ready else False,
    )


async def _get_group_comparison_stats(
    db: AsyncSession,
    group_id: UUID,
    student_id: UUID,
    student_score: float,
    attestation_type: AttestationType,
    subject_id: UUID | None = None,
) -> StudentComparisonStats | None:
    """Получить статистику сравнения с группой."""
    students = await get_group_students(db, group_id)

    attestation_service = AttestationService(db)
    results, _ = await attestation_service.calculate_group_scores_batch(
        group_id=group_id,
        attestation_type=attestation_type,
        students=students,
        subject_id=subject_id,
    )
    if not results:
        return None

    scores = [result.total_score for result in results]
    average = sum(scores) / len(scores)
    sorted_scores = sorted(scores, reverse=True)
    rank = sorted_scores.index(student_score) + 1 if student_score in sorted_scores else len(scores)
    return {"average": round(average, 2), "rank": rank, "total": len(students)}
