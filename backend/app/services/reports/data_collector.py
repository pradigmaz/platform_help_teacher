"""
Модуль сбора данных для публичных отчётов.

Facade для агрегации данных из различных источников.

Attendance contract v1:
    - score и посещаемость студентов в отчётах считаются в окне выбранной аттестации
    - attendance_rate остаётся presentation-метрикой (не score)
    - lesson_history использует отдельную lesson-level метрику
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.group_report import GroupReport, ReportType
from app.schemas.report import PublicReportData, StudentDetailData
from app.services.attestation.service import AttestationService
from app.services.attendance_contract import StudentAttendanceSnapshot

from .attendance_helpers import (
    build_attendance_distribution,
    build_full_attendance_stats,
    build_group_attendance_stats,
    get_recent_lessons_history,
    get_today_lessons_attendance,
    load_group_attendance_snapshots,
)
from .base_helpers import get_filtered_teacher_contacts, get_group, get_group_students, get_user
from .labs_helpers import calculate_grade_distribution, get_group_labs_stats, get_lab_progress
from .notes_helpers import get_students_notes
from .report_builder import build_empty_report
from .semester_helpers import get_semester_info, get_semester_start_date
from .student_builder import process_students
from .student_detail_collector import _get_group_comparison_stats as collect_group_comparison_stats
from .student_detail_collector import collect_student_report_data

logger = logging.getLogger(__name__)


class ReportDataCollector:
    """Сервис сбора данных для отчётов."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_group_report_data(self, report: GroupReport, attestation_type: str = "first") -> PublicReportData:
        """Сбор данных для публичного отчёта группы."""
        att_type = AttestationType.SECOND if attestation_type == "second" else AttestationType.FIRST

        group = await get_group(self.db, report.group_id)
        teacher = await get_user(self.db, report.created_by)
        students = await get_group_students(self.db, report.group_id)

        is_early, max_points, min_passing, is_second_available = await get_semester_info(self.db, att_type)
        semester_start = await get_semester_start_date(self.db)

        # Получаем шкалу оценок
        grade_scale = AttestationSettings.get_grade_scale(att_type)
        # Преобразуем tuple в list для JSON сериализации
        grade_scale_json = {k: list(v) for k, v in grade_scale.items()}

        if not students:
            return build_empty_report(
                report, group, teacher, attestation_type, max_points, min_passing, is_second_available
            )

        # Получаем баллы аттестации
        attestation_service = AttestationService(self.db)
        settings = await attestation_service.get_or_create_settings(att_type)
        period_start, period_end = settings.get_effective_period()
        try:
            attestation_results, _ = await attestation_service.calculate_group_scores_batch(
                group_id=report.group_id,
                attestation_type=att_type,
                students=students,
            )
        except ValueError as exc:
            logger.warning("Report attestation skipped for group %s: %s", report.group_id, exc)
            attestation_results = []

        results_map = {r.student_id: r for r in attestation_results}
        attendance_lessons: list[Lesson] = []
        attendance_snapshots: dict[UUID, StudentAttendanceSnapshot] = {}
        attendance_data = {}
        if report.show_attendance:
            attendance_lessons, attendance_snapshots = await load_group_attendance_snapshots(
                self.db,
                report.group_id,
                students,
                period_start=period_start,
                period_end=period_end,
            )
            attendance_data = build_group_attendance_stats(students, attendance_snapshots)
        labs_data = await get_group_labs_stats(self.db, students, labs_count_override=settings.get_labs_count())

        notes_map = {}
        if report.show_notes:
            notes_map = await get_students_notes(self.db, [s.id for s in students], visible_only=True)

        # Формируем данные студентов
        students_data, passing_count, failing_count, total_score_sum = process_students(
            students, results_map, attendance_data, labs_data, notes_map, report
        )

        # Сортировка
        if report.show_rating and report.show_grades:
            students_data.sort(key=lambda x: x.total_score or 0, reverse=True)
        else:
            students_data.sort(key=lambda x: x.name or "")

        # Графики
        attendance_distribution = None
        attendance_stats = None
        today_lessons = None
        lesson_history = None
        has_subgroups = group.has_subgroups if group and hasattr(group, "has_subgroups") else False

        if report.show_attendance:
            attendance_distribution = build_attendance_distribution(attendance_snapshots)
            lesson_history = await get_recent_lessons_history(
                self.db,
                report.group_id,
                students,
                limit=10,
                period_start_date=period_start,
                period_end_date=period_end,
            )
            attendance_stats = build_full_attendance_stats(
                lessons=attendance_lessons,
                students=students,
                snapshots=attendance_snapshots,
                has_subgroups=has_subgroups,
            )
            today_lessons = await get_today_lessons_attendance(
                self.db,
                report.group_id,
                students,
                show_names=report.show_names,
                period_start_date=period_start,
                period_end_date=period_end,
            )

        lab_progress = None
        lab_progress_by_subgroup = None
        grade_distribution = None
        if report.show_grades:
            lab_progress, lab_progress_by_subgroup = await get_lab_progress(self.db, students, has_subgroups)
            grade_distribution = calculate_grade_distribution(attestation_results)

        return PublicReportData(
            group_code=group.code if group else "",
            group_name=group.name if group else None,
            subject_name=None,
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
            passing_students=passing_count if report.show_grades else None,
            failing_students=failing_count if report.show_grades else None,
            average_score=round(total_score_sum / len(students), 2) if students and report.show_grades else None,
            max_points=max_points,
            min_passing_points=min_passing,
            grade_scale=grade_scale_json if report.show_grades else None,
            attestation_type=attestation_type,
            is_second_available=is_second_available,
            has_subgroups=has_subgroups,
            students=students_data,
            attendance_distribution=attendance_distribution,
            attendance_stats=attendance_stats,
            lab_progress=lab_progress,
            lab_progress_by_subgroup=lab_progress_by_subgroup,
            grade_distribution=grade_distribution,
            today_lessons=today_lessons,
            lesson_history=lesson_history,
        )

    async def get_student_report_data(
        self, report: GroupReport, student_id: UUID, attestation_type: str = "first"
    ) -> StudentDetailData | None:
        """Сбор детальных данных для отчёта по студенту."""
        return await collect_student_report_data(
            db=self.db,
            report=report,
            student_id=student_id,
            attestation_type=attestation_type,
        )

    async def _get_group_comparison_stats(
        self,
        group_id: UUID,
        student_id: UUID,
        student_score: float,
        attestation_type: AttestationType,
    ):
        return await collect_group_comparison_stats(self.db, group_id, student_id, student_score, attestation_type)
