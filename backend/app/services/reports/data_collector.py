"""
Модуль сбора данных для публичных отчётов.

Facade для агрегации данных из различных источников.

Формула посещаемости в отчётах (этот модуль):
    Использует сырые данные attendance без корректировки на EXCUSED.
    EXCUSED включается в знаменатель (expected_lessons не уменьшается).

Отличие от формулы аттестации (services/attestation/attendance_calculator.py):
    В аттестации EXCUSED исключается из знаменателя (adjusted_expected = expected - excused).
    TODO: унифицировать формулы отчётов и аттестации в будущем.
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.group_report import GroupReport, ReportType
from app.schemas.report import PublicReportData, StudentDetailData
from app.services.attestation.service import AttestationService

from .activity_helpers import generate_recommendations, get_student_activity
from .attendance_helpers import (
    get_attendance_distribution,
    get_full_attendance_stats,
    get_group_attendance_stats,
    get_recent_lessons_history,
    get_student_attendance_history,
    get_student_attendance_stats,
    get_today_lessons_attendance,
)
from .base_helpers import get_filtered_teacher_contacts, get_group, get_group_students, get_user
from .labs_helpers import (
    calculate_grade_distribution,
    get_group_labs_stats,
    get_lab_progress,
    get_student_lab_submissions,
)
from .notes_helpers import get_student_notes, get_students_notes
from .report_builder import build_empty_report
from .semester_helpers import get_semester_info, get_semester_start_date
from .student_builder import process_students

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

        # Получаем subject_id преподавателя для этой группы
        subject_id = await self._get_teacher_subject_id(report.created_by, report.group_id)

        if not students:
            return build_empty_report(
                report, group, teacher, attestation_type, max_points, min_passing, is_second_available
            )

        # Получаем баллы аттестации
        attestation_service = AttestationService(self.db)
        attestation_results, _ = await attestation_service.calculate_group_scores_batch(
            group_id=report.group_id, attestation_type=att_type, students=students
        )

        results_map = {r.student_id: r for r in attestation_results}
        attendance_data = await get_group_attendance_stats(self.db, report.group_id, students)
        labs_data = await get_group_labs_stats(self.db, students)

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
            attendance_distribution = await get_attendance_distribution(
                self.db, report.group_id, students, semester_start
            )
            attendance_stats = await get_full_attendance_stats(
                self.db, report.group_id, students, has_subgroups, semester_start, subject_id
            )
            today_lessons = await get_today_lessons_attendance(
                self.db, report.group_id, students, show_names=report.show_names
            )
            lesson_history = await get_recent_lessons_history(
                self.db, report.group_id, students, limit=10, semester_start_date=semester_start
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
        att_type = AttestationType.SECOND if attestation_type == "second" else AttestationType.FIRST

        student = await get_user(self.db, student_id)
        if not student or student.group_id != report.group_id:
            return None

        group = await get_group(self.db, report.group_id)
        is_early, _, _, _ = await get_semester_info(self.db, att_type)

        # Баллы аттестации
        attestation_service = AttestationService(self.db)
        try:
            result = await attestation_service.calculate_student_score(
                student_id=student_id, group_id=report.group_id, attestation_type=att_type
            )
        except Exception as e:
            logger.error(f"Error calculating score for student {student_id}: {e}")
            result = None

        # Посещаемость
        attendance_history = None
        att_stats = {}
        if report.show_attendance:
            attendance_history = await get_student_attendance_history(self.db, student_id, report.group_id)
            att_stats = await get_student_attendance_stats(self.db, student_id, report.group_id)

        # Лабораторные
        lab_submissions = None
        labs_completed = 0
        labs_total = 0
        if report.show_grades:
            lab_submissions = await get_student_lab_submissions(self.db, student_id)
            labs_completed = sum(1 for l in lab_submissions if l.is_submitted)
            labs_total = len(lab_submissions)

        # Активность
        activity_records = None
        total_activity_points = 0.0
        if report.show_grades:
            activity_records = await get_student_activity(self.db, student_id)
            total_activity_points = sum(a.points for a in activity_records)

        # Заметки
        notes = None
        if report.show_notes:
            notes_list = await get_student_notes(self.db, student_id, visible_only=True)
            notes = [n.content for n in notes_list]

        # Сравнение с группой
        group_average = None
        rank_in_group = None
        total_in_group = None
        if report.show_rating and result:
            group_stats = await self._get_group_comparison_stats(
                report.group_id, student_id, result.total_score, att_type
            )
            group_average = group_stats.get("average")
            rank_in_group = group_stats.get("rank")
            total_in_group = group_stats.get("total")

        # Рекомендации
        is_passing = result.is_passing if result else False
        recommendations = None
        if not is_passing:
            recommendations = generate_recommendations(result, att_stats, labs_completed, labs_total)

        return StudentDetailData(
            id=student_id,
            name=student.full_name if report.show_names else None,
            group_code=group.code if group else "",
            total_score=result.total_score if result and report.show_grades else None,
            lab_score=result.breakdown.labs_score if result and report.show_grades else None,
            attendance_score=result.breakdown.attendance_score if result and report.show_grades else None,
            activity_score=result.breakdown.activity_score if result and report.show_grades else None,
            grade=result.grade if result and report.show_grades else None,
            is_passing=is_passing if report.show_grades else None,
            is_early_semester=is_early,
            max_points=result.max_points if result else 100,
            min_passing_points=result.min_passing_points
            if result
            else AttestationSettings.get_min_passing_points(att_type),
            group_average_score=group_average,
            rank_in_group=rank_in_group,
            total_in_group=total_in_group,
            attendance_rate=att_stats.get("rate"),
            attendance_history=attendance_history,
            present_count=att_stats.get("present", 0),
            absent_count=att_stats.get("absent", 0),
            late_count=att_stats.get("late", 0),
            excused_count=att_stats.get("excused", 0),
            total_lessons=att_stats.get("total", 0),
            labs_completed=labs_completed if report.show_grades else None,
            labs_total=labs_total if report.show_grades else None,
            lab_submissions=lab_submissions,
            activity_records=activity_records,
            total_activity_points=total_activity_points if report.show_grades else None,
            notes=notes,
            recommendations=recommendations,
            needs_attention=not is_passing,
        )

    async def _get_group_comparison_stats(
        self, group_id: UUID, student_id: UUID, student_score: float, attestation_type: AttestationType
    ) -> dict:
        """Получить статистику сравнения с группой."""
        students = await get_group_students(self.db, group_id)

        attestation_service = AttestationService(self.db)
        results, _ = await attestation_service.calculate_group_scores_batch(
            group_id=group_id, attestation_type=attestation_type, students=students
        )

        if not results:
            return {}

        scores = [r.total_score for r in results]
        average = sum(scores) / len(scores)
        sorted_scores = sorted(scores, reverse=True)
        rank = sorted_scores.index(student_score) + 1 if student_score in sorted_scores else len(scores)

        return {"average": round(average, 2), "rank": rank, "total": len(students)}

    def apply_visibility_filter(self, data: dict[str, Any], report: GroupReport) -> dict[str, Any]:
        """Применение фильтра видимости к данным."""
        filtered = data.copy()

        if not report.show_names:
            filtered.pop("name", None)
            filtered.pop("full_name", None)

        if not report.show_grades:
            for key in ["total_score", "lab_score", "attendance_score", "activity_score", "grade", "is_passing"]:
                filtered.pop(key, None)

        if not report.show_attendance:
            for key in [
                "attendance_rate",
                "present_count",
                "absent_count",
                "late_count",
                "excused_count",
                "attendance_history",
            ]:
                filtered.pop(key, None)

        if not report.show_notes:
            filtered.pop("notes", None)

        if not report.show_rating:
            filtered.pop("rank_in_group", None)
            filtered.pop("group_average_score", None)

        return filtered

    async def _get_teacher_subject_id(self, teacher_id: UUID, group_id: UUID) -> UUID | None:
        """Получить subject_id для группы из занятий текущего семестра."""
        from app.models.lesson import Lesson

        # Получаем semester_start_date для фильтрации
        semester_start = await get_semester_start_date(self.db)

        # Берём subject_id из занятий группы текущего семестра
        query = select(Lesson.subject_id).where(Lesson.group_id == group_id, Lesson.subject_id.isnot(None))
        if semester_start:
            query = query.where(Lesson.date >= semester_start)
        query = query.order_by(Lesson.date.desc()).limit(1)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
