"""
Модуль сбора данных для публичных отчётов.

Агрегация данных из различных источников.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_report import GroupReport, ReportType
from app.models.group import Group
from app.models.user import User, UserRole
from app.models.attendance import Attendance
from app.models.submission import Submission
from app.models.lab import Lab
from app.models.activity import Activity
from app.models.note import Note
from app.models.attestation_settings import AttestationType
from app.services.attestation.service import AttestationService
from app.schemas.report import (
    PublicReportData,
    PublicStudentData,
    StudentDetailData,
    AttendanceDistribution,
    LabProgress,
    AttendanceRecord,
    LabSubmission,
    ActivityRecord,
)
from app.schemas.user import PublicTeacherContacts

logger = logging.getLogger(__name__)


class ReportDataCollector:
    """Сервис сбора данных для отчётов."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_group_report_data(
        self,
        report: GroupReport
    ) -> PublicReportData:
        """
        Сбор данных для публичного отчёта группы.
        
        Использует AttestationService для расчёта баллов.
        Применяет фильтрацию по настройкам видимости.
        """
        group = await self._get_group(report.group_id)
        teacher = await self._get_user(report.created_by)
        students = await self._get_group_students(report.group_id)
        
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
        attendance_data = await self._get_group_attendance_stats(report.group_id, students)
        labs_data = await self._get_group_labs_stats(students)
        
        notes_map = {}
        if report.show_notes:
            notes_map = await self._get_students_notes([s.id for s in students], visible_only=True)
        
        # Формируем данные студентов
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
        
        # Сортировка
        if report.show_rating and report.show_grades:
            students_data.sort(key=lambda x: x.total_score or 0, reverse=True)
        else:
            students_data.sort(key=lambda x: x.name or "")
        
        # Графики
        attendance_distribution = None
        if report.show_attendance:
            attendance_distribution = await self._get_attendance_distribution(report.group_id, students)
        
        lab_progress = None
        grade_distribution = None
        if report.show_grades:
            lab_progress = await self._get_lab_progress(students)
            grade_distribution = self._calculate_grade_distribution(attestation_results)
        
        return PublicReportData(
            group_code=group.code if group else "",
            group_name=group.name if group else None,
            subject_name=None,
            teacher_name=teacher.full_name if teacher else "Unknown",
            report_type=ReportType(report.report_type),
            generated_at=datetime.now(timezone.utc),
            teacher_contacts=self._get_filtered_teacher_contacts(teacher, "report") if teacher else None,
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
        self,
        report: GroupReport,
        student_id: UUID
    ) -> Optional[StudentDetailData]:
        """Сбор детальных данных для отчёта по студенту."""
        student = await self._get_user(student_id)
        if not student or student.group_id != report.group_id:
            return None
        
        group = await self._get_group(report.group_id)
        
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
            attendance_history = await self._get_student_attendance_history(student_id, report.group_id)
            att_stats = await self._get_student_attendance_stats(student_id, report.group_id)
        
        # Лабораторные
        lab_submissions = None
        labs_completed = 0
        labs_total = 0
        if report.show_grades:
            lab_submissions = await self._get_student_lab_submissions(student_id)
            labs_completed = sum(1 for l in lab_submissions if l.is_submitted)
            labs_total = len(lab_submissions)
        
        # Активность
        activity_records = None
        total_activity_points = 0.0
        if report.show_grades:
            activity_records = await self._get_student_activity(student_id)
            total_activity_points = sum(a.points for a in activity_records)
        
        # Заметки
        notes = None
        if report.show_notes:
            notes_list = await self._get_student_notes(student_id, visible_only=True)
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
            recommendations = self._generate_recommendations(result, att_stats, labs_completed, labs_total)
        
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
    
    def apply_visibility_filter(
        self,
        data: Dict[str, Any],
        report: GroupReport
    ) -> Dict[str, Any]:
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

    # ==================== Helper Methods ====================
    
    async def _get_group(self, group_id: UUID) -> Optional[Group]:
        query = select(Group).where(Group.id == group_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_user(self, user_id: UUID) -> Optional[User]:
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_group_students(self, group_id: UUID) -> List[User]:
        query = (
            select(User)
            .where(
                User.group_id == group_id,
                User.role == UserRole.STUDENT,
                User.is_active == True
            )
            .order_by(User.full_name)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def _get_group_attendance_stats(
        self,
        group_id: UUID,
        students: List[User]
    ) -> Dict[UUID, Dict]:
        student_ids = [s.id for s in students]
        
        query = (
            select(
                Attendance.student_id,
                Attendance.status,
                func.count(Attendance.id).label('count')
            )
            .where(
                Attendance.group_id == group_id,
                Attendance.student_id.in_(student_ids)
            )
            .group_by(Attendance.student_id, Attendance.status)
        )
        result = await self.db.execute(query)
        
        stats = defaultdict(lambda: {'present': 0, 'late': 0, 'excused': 0, 'absent': 0, 'total': 0})
        for row in result.all():
            # Преобразуем enum в строку и в нижний регистр
            status_str = row.status.value.lower() if hasattr(row.status, 'value') else str(row.status).lower()
            stats[row.student_id][status_str] = row.count
            stats[row.student_id]['total'] += row.count
        
        for student_id, data in stats.items():
            total = data['total']
            if total > 0:
                present_equivalent = data['present'] + data['late'] * 0.5 + data['excused'] * 0.5
                data['rate'] = round(present_equivalent / total * 100, 1)
            else:
                data['rate'] = 0.0
        
        return dict(stats)
    
    async def _get_group_labs_stats(self, students: List[User]) -> Dict[UUID, Dict]:
        student_ids = [s.id for s in students]
        
        labs_query = select(Lab)
        labs_result = await self.db.execute(labs_query)
        labs = list(labs_result.scalars().all())
        total_labs = len(labs)
        
        submissions_query = (
            select(Submission.user_id, func.count(Submission.id).label('count'))
            .where(Submission.user_id.in_(student_ids))
            .group_by(Submission.user_id)
        )
        submissions_result = await self.db.execute(submissions_query)
        
        stats = {}
        for row in submissions_result.all():
            stats[row.user_id] = {'completed': row.count, 'total': total_labs}
        
        for student in students:
            if student.id not in stats:
                stats[student.id] = {'completed': 0, 'total': total_labs}
        
        return stats
    
    async def _get_students_notes(
        self,
        student_ids: List[UUID],
        visible_only: bool = True
    ) -> Dict[UUID, List[str]]:
        """Получение заметок для студентов через полиморфную привязку."""
        from app.models.note import EntityType
        
        query = select(Note).where(
            Note.entity_type == EntityType.STUDENT.value,
            Note.entity_id.in_(student_ids)
        )
        
        if visible_only and hasattr(Note, 'is_visible_in_report'):
            query = query.where(Note.is_visible_in_report == True)
        
        result = await self.db.execute(query)
        notes = result.scalars().all()
        
        notes_map = defaultdict(list)
        for note in notes:
            notes_map[note.entity_id].append(note.content)
        
        return dict(notes_map)
    
    async def _get_student_notes(self, student_id: UUID, visible_only: bool = True) -> List[Note]:
        """Получение заметок для студента через полиморфную привязку."""
        from app.models.note import EntityType
        
        query = select(Note).where(
            Note.entity_type == EntityType.STUDENT.value,
            Note.entity_id == student_id
        )
        
        if visible_only and hasattr(Note, 'is_visible_in_report'):
            query = query.where(Note.is_visible_in_report == True)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def _get_attendance_distribution(
        self,
        group_id: UUID,
        students: List[User]
    ) -> AttendanceDistribution:
        student_ids = [s.id for s in students]
        
        query = (
            select(Attendance.status, func.count(Attendance.id).label('count'))
            .where(
                Attendance.group_id == group_id,
                Attendance.student_id.in_(student_ids)
            )
            .group_by(Attendance.status)
        )
        result = await self.db.execute(query)
        
        distribution = AttendanceDistribution()
        for row in result.all():
            # Преобразуем enum в строку и в нижний регистр для соответствия полям модели
            status_str = row.status.value.lower() if hasattr(row.status, 'value') else str(row.status).lower()
            if hasattr(distribution, status_str):
                setattr(distribution, status_str, row.count)
        
        return distribution
    
    async def _get_lab_progress(self, students: List[User]) -> List[LabProgress]:
        student_ids = [s.id for s in students]
        total_students = len(students)
        
        labs_query = select(Lab).order_by(Lab.created_at)
        labs_result = await self.db.execute(labs_query)
        labs = list(labs_result.scalars().all())
        
        submissions_query = (
            select(Submission.lab_id, func.count(func.distinct(Submission.user_id)).label('count'))
            .where(Submission.user_id.in_(student_ids))
            .group_by(Submission.lab_id)
        )
        submissions_result = await self.db.execute(submissions_query)
        submissions_map = {row.lab_id: row.count for row in submissions_result.all()}
        
        progress = []
        for idx, lab in enumerate(labs, 1):
            completed = submissions_map.get(lab.id, 0)
            progress.append(LabProgress(
                lab_name=lab.title or f"Лаб. {idx}",
                completed_count=completed,
                total_students=total_students,
                completion_rate=round(completed / total_students * 100, 1) if total_students > 0 else 0
            ))
        
        return progress
    
    def _calculate_grade_distribution(self, results: List[Any]) -> Dict[str, int]:
        distribution = defaultdict(int)
        for result in results:
            if result.grade:
                distribution[result.grade] += 1
        return dict(distribution)
    
    async def _get_student_attendance_history(
        self,
        student_id: UUID,
        group_id: UUID
    ) -> List[AttendanceRecord]:
        query = (
            select(Attendance)
            .where(
                Attendance.student_id == student_id,
                Attendance.group_id == group_id
            )
            .order_by(Attendance.date.desc())
        )
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        return [
            AttendanceRecord(
                date=r.date, 
                status=r.status.value.lower() if hasattr(r.status, 'value') else str(r.status).lower(), 
                lesson_topic=None
            )
            for r in records
        ]
    
    async def _get_student_attendance_stats(self, student_id: UUID, group_id: UUID) -> Dict:
        query = (
            select(Attendance.status, func.count(Attendance.id).label('count'))
            .where(
                Attendance.student_id == student_id,
                Attendance.group_id == group_id
            )
            .group_by(Attendance.status)
        )
        result = await self.db.execute(query)
        
        stats = {'present': 0, 'late': 0, 'excused': 0, 'absent': 0, 'total': 0}
        for row in result.all():
            # Преобразуем enum в строку и в нижний регистр
            status_str = row.status.value.lower() if hasattr(row.status, 'value') else str(row.status).lower()
            stats[status_str] = row.count
            stats['total'] += row.count
        
        if stats['total'] > 0:
            present_equivalent = stats['present'] + stats['late'] * 0.5 + stats['excused'] * 0.5
            stats['rate'] = round(present_equivalent / stats['total'] * 100, 1)
        else:
            stats['rate'] = 0.0
        
        return stats
    
    async def _get_student_lab_submissions(self, student_id: UUID) -> List[LabSubmission]:
        labs_query = select(Lab).order_by(Lab.created_at)
        labs_result = await self.db.execute(labs_query)
        labs = list(labs_result.scalars().all())
        
        submissions_query = select(Submission).where(Submission.user_id == student_id)
        submissions_result = await self.db.execute(submissions_query)
        submissions = {s.lab_id: s for s in submissions_result.scalars().all()}
        
        result = []
        for idx, lab in enumerate(labs, 1):
            submission = submissions.get(lab.id)
            result.append(LabSubmission(
                lab_id=lab.id,
                lab_name=lab.title or f"Лабораторная {idx}",
                lab_number=idx,
                grade=submission.grade if submission else None,
                max_grade=lab.max_grade or 10,
                submitted_at=submission.submitted_at if submission and hasattr(submission, 'submitted_at') else None,
                is_submitted=submission is not None,
                is_late=False
            ))
        
        return result
    
    async def _get_student_activity(self, student_id: UUID) -> List[ActivityRecord]:
        query = (
            select(Activity)
            .where(Activity.student_id == student_id, Activity.is_active == True)
            .order_by(Activity.created_at.desc())
        )
        result = await self.db.execute(query)
        activities = result.scalars().all()
        
        return [
            ActivityRecord(date=a.created_at, description=a.description or "", points=a.points)
            for a in activities
        ]
    
    async def _get_group_comparison_stats(
        self,
        group_id: UUID,
        student_id: UUID,
        student_score: float
    ) -> Dict:
        students = await self._get_group_students(group_id)
        
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
    
    def _generate_recommendations(
        self,
        result: Any,
        att_stats: Dict,
        labs_completed: int,
        labs_total: int
    ) -> List[str]:
        recommendations = []
        
        if result:
            if result.lab_score < result.max_points * 0.3:
                missing_labs = labs_total - labs_completed
                if missing_labs > 0:
                    recommendations.append(f"Необходимо сдать {missing_labs} лабораторных работ")
            
            if result.attendance_score < result.max_points * 0.1:
                recommendations.append("Рекомендуется улучшить посещаемость занятий")
        
        if att_stats:
            absent_rate = att_stats.get('absent', 0) / max(att_stats.get('total', 1), 1)
            if absent_rate > 0.3:
                recommendations.append(
                    f"Пропущено {att_stats.get('absent', 0)} занятий. "
                    "Рекомендуется посещать все занятия."
                )
        
        if not recommendations:
            recommendations.append("Обратитесь к преподавателю для уточнения требований")
        
        return recommendations
    
    def _build_student_data(
        self,
        student: User,
        result: Any,
        att_stats: Dict,
        lab_stats: Dict,
        notes: List[str],
        report: GroupReport
    ) -> PublicStudentData:
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
        self,
        report: GroupReport,
        group: Optional[Group],
        teacher: Optional[User]
    ) -> PublicReportData:
        return PublicReportData(
            group_code=group.code if group else "",
            group_name=group.name if group else None,
            subject_name=None,
            teacher_name=teacher.full_name if teacher else "Unknown",
            report_type=ReportType(report.report_type),
            generated_at=datetime.now(timezone.utc),
            teacher_contacts=self._get_filtered_teacher_contacts(teacher, "report") if teacher else None,
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
    
    def _get_filtered_teacher_contacts(
        self,
        teacher: User,
        target: str  # "student" or "report"
    ) -> Optional[PublicTeacherContacts]:
        """
        Фильтрация контактов преподавателя по видимости.
        
        target="student" -> visibility in ("student", "both")
        target="report" -> visibility in ("report", "both")
        """
        contacts = teacher.contacts or {}
        visibility = teacher.contact_visibility or {}
        
        if not contacts:
            return None
        
        allowed_visibility = ("student", "both") if target == "student" else ("report", "both")
        
        filtered = {}
        for field, value in contacts.items():
            vis = visibility.get(field, "none")
            if vis in allowed_visibility and value:
                filtered[field] = value
        
        if not filtered:
            return None
        
        return PublicTeacherContacts(
            telegram=filtered.get("telegram"),
            vk=filtered.get("vk"),
            max=filtered.get("max"),
            teacher_name=teacher.full_name,
        )
