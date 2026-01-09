"""
Расчёт баллов для одного студента (автобалансировка).
"""
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.attendance import Attendance, AttendanceStatus
from app.models.user import User
from app.models.activity import Activity
from app.models.lesson_grade import LessonGrade
from app.models.lesson import Lesson
from app.models.student_transfer import StudentTransfer
from app.schemas.attestation import AttestationResult, ComponentBreakdown

from .calculator import AttestationCalculator
from .settings import AttestationSettingsManager
from .helpers import filter_lessons_by_subgroup

logger = logging.getLogger(__name__)


class StudentScoreCalculator:
    """Калькулятор баллов для одного студента."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.calculator = AttestationCalculator()
        self.settings_manager = AttestationSettingsManager(db)
    
    async def calculate(
        self,
        student_id: UUID,
        group_id: UUID,
        attestation_type: AttestationType,
        extra_activity_points: float = 0.0
    ) -> AttestationResult:
        """Расчёт баллов аттестации для студента."""
        settings = await self.settings_manager.get_or_create_settings(attestation_type)
        
        student = await self._get_student(student_id)
        if not student:
            raise ValueError(f"Студент {student_id} не найден")
        
        # Получаем данные из текущей группы
        lesson_grades = await self._get_lesson_grades(student_id, settings)
        attendance_records = await self._get_attendance(student_id, group_id, student.subgroup, settings)
        db_activity_points = await self._get_activity_points(student_id, attestation_type)
        
        # Получаем снапшоты переводов и объединяем данные
        transfers = await self._get_transfers_in_period(student_id, attestation_type, settings)
        transfer_attendance = self._merge_transfer_attendance(transfers)
        transfer_lab_grades = self._merge_transfer_lab_grades(transfers)
        transfer_activity = self._sum_transfer_activity(transfers)
        
        # Расчёт компонентов с учётом переводов
        lab_result = self.calculator.calculate_labs(
            lesson_grades, settings, transfer_lab_grades
        )
        attendance_result = self.calculator.calculate_attendance(
            attendance_records, settings, transfer_attendance
        )
        
        # Текущий балл (без активности)
        current_score = lab_result.score + attendance_result.score
        
        # Активность с учётом лимита (включая снапшоты переводов)
        total_activity = db_activity_points + extra_activity_points + transfer_activity
        activity_score, bonus_blocked = self.calculator.calculate_activity(
            total_activity, current_score, settings
        )
        
        # Итог
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
            attestation_type=attestation_type,
            total_score=total_score,
            grade=grade,
            is_passing=is_passing,
            max_points=settings.attestation_type.max_points,
            min_passing_points=AttestationSettings.get_min_passing_points(attestation_type),
            breakdown=breakdown,
        )
    
    async def _get_student(self, student_id: UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == student_id))
        return result.scalar_one_or_none()
    
    async def _get_lesson_grades(
        self, student_id: UUID, settings: AttestationSettings
    ) -> List[LessonGrade]:
        query = (
            select(LessonGrade)
            .join(Lesson, LessonGrade.lesson_id == Lesson.id)
            .where(LessonGrade.student_id == student_id)
        )
        if settings.period_start_date:
            query = query.where(Lesson.date >= settings.period_start_date)
        if settings.period_end_date:
            query = query.where(Lesson.date <= settings.period_end_date)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def _get_attendance(
        self, student_id: UUID, group_id: UUID, subgroup: int | None, settings: AttestationSettings
    ) -> List[Attendance]:
        # Сначала получаем релевантные занятия
        lessons_query = select(Lesson).where(Lesson.group_id == group_id)
        if settings.period_start_date:
            lessons_query = lessons_query.where(Lesson.date >= settings.period_start_date)
        if settings.period_end_date:
            lessons_query = lessons_query.where(Lesson.date <= settings.period_end_date)
        lessons_query = filter_lessons_by_subgroup(lessons_query, subgroup)
        
        lessons_result = await self.db.execute(lessons_query)
        relevant_dates = {l.date for l in lessons_result.scalars().all()}
        
        if not relevant_dates:
            return []
        
        # Посещаемость по этим датам
        att_query = select(Attendance).where(
            Attendance.student_id == student_id,
            Attendance.group_id == group_id,
            Attendance.date.in_(relevant_dates)
        )
        result = await self.db.execute(att_query)
        return list(result.scalars().all())
    
    async def _get_activity_points(
        self, student_id: UUID, attestation_type: AttestationType
    ) -> float:
        query = select(func.sum(Activity.points)).where(
            Activity.student_id == student_id,
            Activity.attestation_type == attestation_type,
            Activity.is_active == True
        )
        result = await self.db.execute(query)
        return result.scalar() or 0.0

    async def _get_transfers_in_period(
        self,
        student_id: UUID,
        attestation_type: AttestationType,
        settings: AttestationSettings
    ) -> List[StudentTransfer]:
        """Получить переводы студента в периоде аттестации."""
        query = select(StudentTransfer).where(
            StudentTransfer.student_id == student_id,
            StudentTransfer.attestation_type == attestation_type
        )
        if settings.period_start_date:
            query = query.where(StudentTransfer.transfer_date >= settings.period_start_date)
        if settings.period_end_date:
            query = query.where(StudentTransfer.transfer_date <= settings.period_end_date)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _merge_transfer_attendance(
        self, transfers: List[StudentTransfer]
    ) -> Optional[dict]:
        """Объединить снапшоты посещаемости из переводов."""
        if not transfers:
            return None
        
        merged = {
            "total_lessons": 0,
            "present": 0,
            "late": 0,
            "excused": 0,
            "absent": 0
        }
        for t in transfers:
            data = t.attendance_data or {}
            merged["total_lessons"] += data.get("total_lessons", 0)
            merged["present"] += data.get("present", 0)
            merged["late"] += data.get("late", 0)
            merged["excused"] += data.get("excused", 0)
            merged["absent"] += data.get("absent", 0)
        
        return merged if merged["total_lessons"] > 0 else None

    def _merge_transfer_lab_grades(
        self, transfers: List[StudentTransfer]
    ) -> List[dict]:
        """Объединить снапшоты оценок за лабы из переводов."""
        all_grades = []
        for t in transfers:
            grades = t.lab_grades_data or []
            all_grades.extend(grades)
        return all_grades

    def _sum_transfer_activity(self, transfers: List[StudentTransfer]) -> float:
        """Суммировать баллы активности из снапшотов переводов."""
        return sum(t.activity_points or 0.0 for t in transfers)
