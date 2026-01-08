"""
Модуль сбора данных для публичных отчётов.

Facade для агрегации данных из различных источников.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_report import GroupReport, ReportType
from app.models.group import Group
from app.models.user import User
from app.models.attestation_settings import AttestationType
from app.services.attestation.service import AttestationService
from app.schemas.report import (
    PublicReportData,
    PublicStudentData,
    StudentDetailData,
)

from .base_helpers import (
    get_group, get_user, get_group_students, get_filtered_teacher_contacts
)
from .attendance_helpers import (
    get_group_attendance_stats, get_attendance_distribution,
    get_student_attendance_history, get_student_attendance_stats
)
from .labs_helpers import (
    get_group_labs_stats, get_lab_progress, 
    get_student_lab_submissions, calculate_grade_distribution
)
from .notes_helpers import get_students_notes, get_student_notes
from .activity_helpers import get_student_activity, generate_recommendations

logger = logging.getLogger(__name__)


class ReportDataCollector:
    """Сервис сбора данных для отчётов."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_group_report_data(self, report: GroupReport) -> PublicReportData:
        """Сбор данных для публичного отчёта группы."""
        group = await get_group(self.db, report.group_id)
        teacher = await get_user(self.db, report.created_by)
        students = await get_group_students(self.db, report.group_id)
        
        if not students:
            return self._build_empty_report_data(report, group, teacher)
        
        # Получаем баллы аттестации
        attestation_service = AttestationService(self.db)
        attestation_results, _ = await attestation_service.calculate_group_scores_batch(
            group_id=report.group_id,
            attestation_type=AttestationType.FIRST,
            students=students
        )
        
        results_map = {r.student_id: r for r in attestation_results}
        attendance_data = await get_group_attendance_stats(self.db, report.group_id, students)
        labs_data = await get_group_labs_stats(self.db, students)
        
        notes_map = {}
        if report.show_notes:
            notes_map = await get_students_notes(self.db, [s.id for s in students], visible_only=True)
        
        # Формируем данные студентов
        students_data, passing_count, failing_count, total_score_sum = self._process_students(
            students, results_map, attendance_data, labs_data, notes_map, report
        )
        
        # Сортировка
        if report.show_rating and report.show_grades:
            students_data.sort(key=lambda x: x.total_score or 0, reverse=True)
        else:
            students_data.sort(key=lambda x: x.name or "")
        
        # Графики
        attendance_distribution = None
        if report.show_attendance:
            attendance_distribution = await get_attendance_distribution(self.db, report.group_id, students)
        
        lab_progress = None
        grade_distribution = None
        if report.show_grades:
            lab_progress = await get_lab_progress(self.db, students)
            grade_distribution = calculate_grade_distribution(attestation_results)
        
        return PublicReportData(
            group_code=group.code if group else "",
            group_name=group.name if group else None,
            subject_name=None,
            teacher_name=teacher.full_name if teacher else "Unknown",
            report_type=ReportType(report.report_type),
            generated_at=datetime.now(timezone.utc),
            teacher_contacts=get_filtered_teacher_contacts(teacher, "report") if teacher else None,
            show_names=report.show_names,
            show_grades=report.show_grades,
            show_attendance=report.show_attendance,
            show_notes=report.show_notes,
            show_rating=report.show_rating,
            total_students=len(students),
            passing_students=passing_count if report.show_grades else None,
            failing_students=failing_count if report.show_grades else None,
            average_score=round(total_score_sum / len(students), 2) if students and report.show_grades else None,
            students=students_data,
            attendance_distribution=attendance_distribution,
            lab_progress=lab_progress,
            grade_distribution=grade_distribution,
        )
    
    async def get_student_report_data(
        self, report: GroupReport, student_id: UUID
    ) -> Optional[StudentDetailData]:
        """Сбор детальных данных для отчёта по студенту."""
        student = await get_user(self.db, student_id)
        if not student or student.group_id != report.group_id:
            return None
        
        group = await get_group(self.db, report.group_id)
        
        # Баллы аттестации
        attestation_service = AttestationService(self.db)
        try:
            result = await attestation_service.calculate_student_score(
                student_id=student_id,
                group_id=report.group_id,
                attestation_type=AttestationType.FIRST
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
                report.group_id, student_id, result.total_score
            )
            group_average = group_stats.get('average')
            rank_in_group = group_stats.get('rank')
            total_in_group = group_stats.get('total')
        
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
            lab_score=result.lab_score if result and report.show_grades else None,
            attendance_score=result.attendance_score if result and report.show_grades else None,
            activity_score=result.activity_score if result and report.show_grades else None,
            grade=result.grade if result and report.show_grades else None,
            is_passing=is_passing if report.show_grades else None,
            max_points=result.max_points if result else 100,
            min_passing_points=result.min_passing_points if result else 61,
            group_average_score=group_average,
            rank_in_group=rank_in_group,
            total_in_group=total_in_group,
            attendance_rate=att_stats.get('rate'),
            attendance_history=attendance_history,
            present_count=att_stats.get('present', 0),
            absent_count=att_stats.get('absent', 0),
            late_count=att_stats.get('late', 0),
            excused_count=att_stats.get('excused', 0),
            total_lessons=att_stats.get('total', 0),
            labs_completed=labs_completed if report.show_grades else None,
            labs_total=labs_total if report.show_grades else None,
            lab_submissions=lab_submissions,
            activity_records=activity_records,
            total_activity_points=total_activity_points if report.show_grades else None,
            notes=notes,
            recommendations=recommendations,
            needs_attention=not is_passing,
        )
    
    def apply_visibility_filter(self, data: Dict[str, Any], report: GroupReport) -> Dict[str, Any]:
        """Применение фильтра видимости к данным."""
        filtered = data.copy()
        
        if not report.show_names:
            filtered.pop('name', None)
            filtered.pop('full_name', None)
        
        if not report.show_grades:
            for key in ['total_score', 'lab_score', 'attendance_score', 
                       'activity_score', 'grade', 'is_passing']:
                filtered.pop(key, None)
        
        if not report.show_attendance:
            for key in ['attendance_rate', 'present_count', 'absent_count',
                       'late_count', 'excused_count', 'attendance_history']:
                filtered.pop(key, None)
        
        if not report.show_notes:
            filtered.pop('notes', None)
        
        if not report.show_rating:
            filtered.pop('rank_in_group', None)
            filtered.pop('group_average_score', None)
        
        return filtered

    # ==================== Private Methods ====================
    
    def _process_students(
        self, students, results_map, attendance_data, labs_data, notes_map, report
    ):
        """Обработка данных студентов."""
        students_data = []
        passing_count = 0
        failing_count = 0
        total_score_sum = 0.0
        
        for student in students:
            result = results_map.get(student.id)
            att_stats = attendance_data.get(student.id, {})
            lab_stats = labs_data.get(student.id, {})
            
            is_passing = result.is_passing if result else False
            if is_passing:
                passing_count += 1
            else:
                failing_count += 1
            
            if result:
                total_score_sum += result.total_score
            
            student_data = self._build_student_data(
                student, result, att_stats, lab_stats,
                notes_map.get(student.id, []), report
            )
            students_data.append(student_data)
        
        return students_data, passing_count, failing_count, total_score_sum
    
    async def _get_group_comparison_stats(
        self, group_id: UUID, student_id: UUID, student_score: float
    ) -> Dict:
        """Получить статистику сравнения с группой."""
        students = await get_group_students(self.db, group_id)
        
        attestation_service = AttestationService(self.db)
        results, _ = await attestation_service.calculate_group_scores_batch(
            group_id=group_id,
            attestation_type=AttestationType.FIRST,
            students=students
        )
        
        if not results:
            return {}
        
        scores = [r.total_score for r in results]
        average = sum(scores) / len(scores)
        sorted_scores = sorted(scores, reverse=True)
        rank = sorted_scores.index(student_score) + 1 if student_score in sorted_scores else len(scores)
        
        return {'average': round(average, 2), 'rank': rank, 'total': len(students)}
    
    def _build_student_data(
        self, student: User, result: Any, att_stats: Dict,
        lab_stats: Dict, notes: List[str], report: GroupReport
    ) -> PublicStudentData:
        """Построить данные студента."""
        is_passing = result.is_passing if result else False
        
        return PublicStudentData(
            id=student.id,
            name=student.full_name if report.show_names else None,
            total_score=result.total_score if result and report.show_grades else None,
            lab_score=result.lab_score if result and report.show_grades else None,
            attendance_score=result.attendance_score if result and report.show_grades else None,
            activity_score=result.activity_score if result and report.show_grades else None,
            grade=result.grade if result and report.show_grades else None,
            is_passing=is_passing if report.show_grades else None,
            attendance_rate=att_stats.get('rate') if report.show_attendance else None,
            present_count=att_stats.get('present') if report.show_attendance else None,
            absent_count=att_stats.get('absent') if report.show_attendance else None,
            late_count=att_stats.get('late') if report.show_attendance else None,
            excused_count=att_stats.get('excused') if report.show_attendance else None,
            labs_completed=lab_stats.get('completed') if report.show_grades else None,
            labs_total=lab_stats.get('total') if report.show_grades else None,
            needs_attention=not is_passing,
            notes=notes if report.show_notes and notes else None,
        )
    
    def _build_empty_report_data(
        self, report: GroupReport, group: Optional[Group], teacher: Optional[User]
    ) -> PublicReportData:
        """Построить пустой отчёт."""
        return PublicReportData(
            group_code=group.code if group else "",
            group_name=group.name if group else None,
            subject_name=None,
            teacher_name=teacher.full_name if teacher else "Unknown",
            report_type=ReportType(report.report_type),
            generated_at=datetime.now(timezone.utc),
            teacher_contacts=get_filtered_teacher_contacts(teacher, "report") if teacher else None,
            show_names=report.show_names,
            show_grades=report.show_grades,
            show_attendance=report.show_attendance,
            show_notes=report.show_notes,
            show_rating=report.show_rating,
            total_students=0,
            passing_students=0 if report.show_grades else None,
            failing_students=0 if report.show_grades else None,
            average_score=None,
            students=[],
            attendance_distribution=None,
            lab_progress=None,
            grade_distribution=None,
        )
