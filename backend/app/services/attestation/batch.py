"""
Пакетные операции расчёта баллов (автобалансировка).
"""
import logging
from typing import Optional, List
from uuid import UUID
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.attendance import Attendance
from app.models.user import User
from app.models.activity import Activity
from app.models.lesson_grade import LessonGrade
from app.models.lesson import Lesson
from app.models.group import Group
from app.models.student_transfer import StudentTransfer
from app.models import UserRole
from app.schemas.attestation import (
    AttestationResult,
    ComponentBreakdown,
    CalculationErrorInfo,
)

from .calculator import AttestationCalculator
from .settings import AttestationSettingsManager

logger = logging.getLogger(__name__)


class BatchScoreCalculator:
    """Калькулятор пакетных операций."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.calculator = AttestationCalculator()
        self.settings_manager = AttestationSettingsManager(db)
    
    async def calculate_group_batch(
        self,
        group_id: UUID,
        attestation_type: AttestationType,
        students: Optional[List[User]] = None
    ) -> tuple[List[AttestationResult], List[CalculationErrorInfo]]:
        """Пакетный расчёт для группы."""
        settings = await self.settings_manager.get_or_create_settings(attestation_type)
        
        if not students:
            students_query = select(User).where(
                User.group_id == group_id,
                User.role == UserRole.STUDENT,
                User.is_active == True
            )
            students_result = await self.db.execute(students_query)
            students = list(students_result.scalars().all())
            
        if not students:
            return [], []
        
        # Batch загрузка данных
        student_ids = [s.id for s in students]
        
        # Занятия группы
        lessons = await self._get_lessons(group_id, settings)
        lessons_by_subgroup = self._group_lessons_by_subgroup(lessons)
        
        # Оценки за лабы
        lesson_grades_map = await self._get_lesson_grades_batch(student_ids, settings)
        
        # Посещаемость
        attendance_map = await self._get_attendance_batch(group_id, student_ids)
        
        # Активность
        activity_map = await self._get_activity_batch(student_ids, attestation_type)
        
        # Переводы студентов в периоде
        transfers_map = await self._get_transfers_batch(student_ids, attestation_type, settings)
        
        # Расчёт для каждого студента
        results, errors = [], []
        
        for student in students:
            try:
                result = self._calculate_student(
                    student, settings, lessons_by_subgroup,
                    lesson_grades_map, attendance_map, activity_map, transfers_map
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error for student {student.id}: {e}")
                errors.append(CalculationErrorInfo(
                    student_id=student.id,
                    student_name=student.full_name or str(student.id),
                    error=str(e)
                ))
        
        return results, errors
    
    def _calculate_student(
        self,
        student: User,
        settings: AttestationSettings,
        lessons_by_subgroup: dict,
        lesson_grades_map: dict,
        attendance_map: dict,
        activity_map: dict,
        transfers_map: dict
    ) -> AttestationResult:
        """Расчёт для одного студента (sync)."""
        # Релевантные занятия для подгруппы
        subgroup = student.subgroup
        if subgroup is not None:
            relevant_lessons = lessons_by_subgroup.get(None, []) + lessons_by_subgroup.get(subgroup, [])
        else:
            relevant_lessons = lessons_by_subgroup.get(None, [])
        
        relevant_dates = {l.date for l in relevant_lessons}
        
        # Данные студента
        lesson_grades = lesson_grades_map.get(student.id, [])
        all_attendance = attendance_map.get(student.id, [])
        attendance = [a for a in all_attendance if a.date in relevant_dates]
        activity_points = activity_map.get(student.id, 0.0)
        
        # Данные из снапшотов переводов
        student_transfers = transfers_map.get(student.id, [])
        transfer_attendance = self._merge_transfer_attendance(student_transfers)
        transfer_lab_grades = self._merge_transfer_lab_grades(student_transfers)
        transfer_activity = self._sum_transfer_activity(student_transfers)
        
        # Расчёт с учётом переводов
        lab_result = self.calculator.calculate_labs(lesson_grades, settings, transfer_lab_grades)
        attendance_result = self.calculator.calculate_attendance(attendance, settings, transfer_attendance)
        
        current_score = lab_result.score + attendance_result.score
        total_activity = activity_points + transfer_activity
        activity_score, bonus_blocked = self.calculator.calculate_activity(
            total_activity, current_score, settings
        )
        
        total_score, grade, is_passing = self.calculator.calculate_total(
            lab_result, attendance_result, activity_score, settings
        )
        
        breakdown = ComponentBreakdown(
            labs_score=lab_result.score,
            labs_count=lab_result.labs_count,
            labs_max=lab_result.max_score,
            attendance_score=attendance_result.score,
            attendance_ratio=attendance_result.ratio,
            attendance_max=attendance_result.max_score,
            total_classes=attendance_result.total_classes,
            present_count=attendance_result.present_count,
            late_count=attendance_result.late_count,
            excused_count=attendance_result.excused_count,
            absent_count=attendance_result.absent_count,
            activity_score=activity_score,
            activity_max=settings.get_max_component_points(settings.activity_reserve),
            bonus_blocked=bonus_blocked,
        )
        
        return AttestationResult(
            student_id=student.id,
            student_name=student.full_name or str(student.id),
            attestation_type=settings.attestation_type,
            total_score=total_score,
            grade=grade,
            is_passing=is_passing,
            max_points=settings.attestation_type.max_points,
            min_passing_points=AttestationSettings.get_min_passing_points(settings.attestation_type),
            breakdown=breakdown,
        )
    
    async def _get_lessons(self, group_id: UUID, settings: AttestationSettings) -> List[Lesson]:
        query = select(Lesson).where(Lesson.group_id == group_id)
        if settings.period_start_date:
            query = query.where(Lesson.date >= settings.period_start_date)
        if settings.period_end_date:
            query = query.where(Lesson.date <= settings.period_end_date)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    def _group_lessons_by_subgroup(self, lessons: List[Lesson]) -> dict:
        grouped = defaultdict(list)
        for lesson in lessons:
            grouped[lesson.subgroup].append(lesson)
        return grouped
    
    async def _get_lesson_grades_batch(
        self, student_ids: List[UUID], settings: AttestationSettings
    ) -> dict:
        query = (
            select(LessonGrade)
            .join(Lesson, LessonGrade.lesson_id == Lesson.id)
            .where(LessonGrade.student_id.in_(student_ids))
        )
        if settings.period_start_date:
            query = query.where(Lesson.date >= settings.period_start_date)
        if settings.period_end_date:
            query = query.where(Lesson.date <= settings.period_end_date)
        
        result = await self.db.execute(query)
        
        grouped = defaultdict(list)
        for lg in result.scalars().all():
            grouped[lg.student_id].append(lg)
        return grouped
    
    async def _get_attendance_batch(self, group_id: UUID, student_ids: List[UUID]) -> dict:
        query = select(Attendance).where(
            Attendance.group_id == group_id,
            Attendance.student_id.in_(student_ids)
        )
        result = await self.db.execute(query)
        
        grouped = defaultdict(list)
        for a in result.scalars().all():
            grouped[a.student_id].append(a)
        return grouped
    
    async def _get_activity_batch(
        self, student_ids: List[UUID], attestation_type: AttestationType
    ) -> dict:
        query = select(Activity.student_id, func.sum(Activity.points)).where(
            Activity.student_id.in_(student_ids),
            Activity.attestation_type == attestation_type,
            Activity.is_active == True
        ).group_by(Activity.student_id)
        
        result = await self.db.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def _get_transfers_batch(
        self,
        student_ids: List[UUID],
        attestation_type: AttestationType,
        settings: AttestationSettings
    ) -> dict:
        """Batch-загрузка переводов студентов в периоде."""
        query = select(StudentTransfer).where(
            StudentTransfer.student_id.in_(student_ids),
            StudentTransfer.attestation_type == attestation_type
        )
        if settings.period_start_date:
            query = query.where(StudentTransfer.transfer_date >= settings.period_start_date)
        if settings.period_end_date:
            query = query.where(StudentTransfer.transfer_date <= settings.period_end_date)
        
        result = await self.db.execute(query)
        
        grouped = defaultdict(list)
        for t in result.scalars().all():
            grouped[t.student_id].append(t)
        return grouped

    def _merge_transfer_attendance(self, transfers: List[StudentTransfer]) -> Optional[dict]:
        """Объединить снапшоты посещаемости из переводов."""
        if not transfers:
            return None
        
        merged = {"total_lessons": 0, "present": 0, "late": 0, "excused": 0, "absent": 0}
        for t in transfers:
            data = t.attendance_data or {}
            merged["total_lessons"] += data.get("total_lessons", 0)
            merged["present"] += data.get("present", 0)
            merged["late"] += data.get("late", 0)
            merged["excused"] += data.get("excused", 0)
            merged["absent"] += data.get("absent", 0)
        
        return merged if merged["total_lessons"] > 0 else None

    def _merge_transfer_lab_grades(self, transfers: List[StudentTransfer]) -> List[dict]:
        """Объединить снапшоты оценок за лабы из переводов."""
        all_grades = []
        for t in transfers:
            all_grades.extend(t.lab_grades_data or [])
        return all_grades

    def _sum_transfer_activity(self, transfers: List[StudentTransfer]) -> float:
        """Суммировать баллы активности из снапшотов переводов."""
        return sum(t.activity_points or 0.0 for t in transfers)
