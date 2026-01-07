"""
Модуль расчёта баллов для одного студента.
"""
import logging
from typing import List
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.attendance import Attendance, AttendanceStatus
from app.models.user import User
from app.models.activity import Activity
from app.models.lesson_grade import LessonGrade
from app.models.lesson import Lesson
from app.models.student_transfer import StudentTransfer
from app.schemas.attestation import (
    AttestationResult,
    ComponentBreakdown,
)

from .models import LabScoreResult, AttendanceScoreResult
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
        activity_points: float = 0.0
    ) -> AttestationResult:
        """Расчёт баллов аттестации для студента."""
        att_settings = await self.settings_manager.get_or_create_settings(attestation_type)
        
        # Получаем данные студента
        student_query = select(User).where(User.id == student_id)
        student_result = await self.db.execute(student_query)
        student = student_result.scalar_one_or_none()
        
        if not student:
            raise ValueError(f"Студент с ID {student_id} не найден")
        
        # Проверяем наличие переводов в периоде аттестации
        transfers = await self._get_transfers(student_id, attestation_type, att_settings)
        
        # Если есть переводы - используем расчёт с учётом снапшота
        if transfers:
            return await self._calculate_with_transfers(
                student, group_id, attestation_type, att_settings, transfers, activity_points
            )
        
        # Обычный расчёт без переводов
        return await self._calculate_normal(
            student, group_id, attestation_type, att_settings, activity_points
        )
    
    async def _get_transfers(
        self,
        student_id: UUID,
        attestation_type: AttestationType,
        att_settings: AttestationSettings
    ) -> List[StudentTransfer]:
        """Получение переводов студента в периоде аттестации."""
        transfers_query = (
            select(StudentTransfer)
            .where(
                StudentTransfer.student_id == student_id,
                StudentTransfer.attestation_type == attestation_type.value
            )
        )
        if att_settings.period_start_date:
            transfers_query = transfers_query.where(
                StudentTransfer.transfer_date >= att_settings.period_start_date
            )
        if att_settings.period_end_date:
            transfers_query = transfers_query.where(
                StudentTransfer.transfer_date <= att_settings.period_end_date
            )
        transfers_query = transfers_query.order_by(StudentTransfer.transfer_date.desc())
        transfers_result = await self.db.execute(transfers_query)
        return list(transfers_result.scalars().all())

    async def _calculate_normal(
        self,
        student: User,
        group_id: UUID,
        attestation_type: AttestationType,
        att_settings: AttestationSettings,
        activity_points: float = 0.0
    ) -> AttestationResult:
        """Обычный расчёт без переводов."""
        student_subgroup = student.subgroup
        
        # Получаем релевантные занятия для подгруппы студента
        lessons_query = select(Lesson).where(Lesson.group_id == group_id)
        if att_settings.period_start_date:
            lessons_query = lessons_query.where(Lesson.date >= att_settings.period_start_date)
        if att_settings.period_end_date:
            lessons_query = lessons_query.where(Lesson.date <= att_settings.period_end_date)
        
        # Фильтр по подгруппе
        lessons_query = filter_lessons_by_subgroup(lessons_query, student_subgroup)
        
        lessons_result = await self.db.execute(lessons_query)
        relevant_lessons = list(lessons_result.scalars().all())
        relevant_dates = {l.date for l in relevant_lessons}
        
        # Получаем оценки за лабы из журнала
        lesson_grades_query = (
            select(LessonGrade)
            .join(Lesson, LessonGrade.lesson_id == Lesson.id)
            .where(LessonGrade.student_id == student.id)
        )
        if att_settings.period_start_date:
            lesson_grades_query = lesson_grades_query.where(Lesson.date >= att_settings.period_start_date)
        if att_settings.period_end_date:
            lesson_grades_query = lesson_grades_query.where(Lesson.date <= att_settings.period_end_date)
        
        lesson_grades_result = await self.db.execute(lesson_grades_query)
        lesson_grades = list(lesson_grades_result.scalars().all())
        
        # Получаем записи посещаемости только по релевантным датам
        attendance_query = select(Attendance).where(
            Attendance.student_id == student.id,
            Attendance.group_id == group_id
        )
        if relevant_dates:
            attendance_query = attendance_query.where(Attendance.date.in_(relevant_dates))
        else:
            attendance_query = attendance_query.where(False)
        
        attendance_result = await self.db.execute(attendance_query)
        attendance_records = list(attendance_result.scalars().all())
        
        # Получаем баллы за активность из БД
        db_activity_query = select(func.sum(Activity.points)).where(
            Activity.student_id == student.id,
            Activity.attestation_type == attestation_type,
            Activity.is_active == True
        )
        db_activity_result = await self.db.execute(db_activity_query)
        db_activity_points = db_activity_result.scalar() or 0.0
        
        total_activity_points = db_activity_points + activity_points
        
        # Расчёт компонентов
        lab_result = self.calculator.calculate_lesson_grades_score(lesson_grades, att_settings)
        attendance_result_calc = self.calculator.calculate_attendance_score(attendance_records, att_settings)
        activity_score = self.calculator.calculate_activity_score(total_activity_points, att_settings)
        
        # Итоговый расчёт
        total_score, grade, is_passing = self.calculator.calculate_total_score(
            lab_result, attendance_result_calc, activity_score, att_settings
        )
        
        # Формируем детализацию
        breakdown = ComponentBreakdown(
            labs_raw_score=lab_result.raw_score,
            labs_weighted_score=lab_result.weighted_score,
            labs_count=lab_result.labs_count,
            labs_required=lab_result.required_count,
            labs_bonus=lab_result.bonus_points,
            attendance_raw_score=attendance_result_calc.raw_score,
            attendance_weighted_score=attendance_result_calc.weighted_score,
            attendance_total_classes=attendance_result_calc.total_classes,
            attendance_present=attendance_result_calc.present_count,
            attendance_late=attendance_result_calc.late_count,
            attendance_excused=attendance_result_calc.excused_count,
            attendance_absent=attendance_result_calc.absent_count,
            activity_raw_score=total_activity_points,
            activity_weighted_score=activity_score
        )
        
        return AttestationResult(
            student_id=student.id,
            student_name=student.full_name or str(student.id),
            attestation_type=attestation_type,
            total_score=round(total_score, 2),
            lab_score=round(lab_result.weighted_score, 2),
            attendance_score=round(attendance_result_calc.weighted_score, 2),
            activity_score=round(activity_score, 2),
            grade=grade,
            is_passing=is_passing,
            max_points=AttestationSettings.get_max_points(attestation_type),
            min_passing_points=AttestationSettings.get_min_passing_points(attestation_type),
            components_breakdown=breakdown
        )

    async def _calculate_with_transfers(
        self,
        student: User,
        current_group_id: UUID,
        attestation_type: AttestationType,
        att_settings: AttestationSettings,
        transfers: List[StudentTransfer],
        activity_points: float = 0.0
    ) -> AttestationResult:
        """Расчёт баллов с учётом переводов (объединение снапшота и новых данных)."""
        # Берём последний перевод
        transfer = transfers[0]
        
        # === СТАРЫЕ ДАННЫЕ (из снапшота) ===
        old_att = transfer.attendance_data
        old_total_lessons = old_att.get("total_lessons", 0)
        old_present = old_att.get("present", 0)
        old_late = old_att.get("late", 0)
        old_excused = old_att.get("excused", 0)
        old_absent = old_att.get("absent", 0)
        
        old_lab_grades = {
            g.get("work_number"): g.get("grade")
            for g in transfer.lab_grades_data
            if g.get("work_number") is not None
        }
        old_activity = transfer.activity_points
        
        # === НОВЫЕ ДАННЫЕ (после перевода) ===
        current_subgroup = student.subgroup
        
        # Релевантные занятия в НОВОЙ группе после перевода
        new_lessons_query = select(Lesson).where(
            Lesson.group_id == current_group_id,
            Lesson.date > transfer.transfer_date
        )
        if att_settings.period_end_date:
            new_lessons_query = new_lessons_query.where(Lesson.date <= att_settings.period_end_date)
        
        # Фильтр по подгруппе
        new_lessons_query = filter_lessons_by_subgroup(new_lessons_query, current_subgroup)
        
        new_lessons_result = await self.db.execute(new_lessons_query)
        new_lessons = list(new_lessons_result.scalars().all())
        new_dates = {l.date for l in new_lessons}
        
        # Посещаемость после перевода
        new_present, new_late, new_excused, new_absent = 0, 0, 0, 0
        if new_dates:
            new_att_query = select(Attendance).where(
                Attendance.student_id == student.id,
                Attendance.group_id == current_group_id,
                Attendance.date.in_(new_dates)
            )
            new_att_result = await self.db.execute(new_att_query)
            new_records = list(new_att_result.scalars().all())
            
            new_present = sum(1 for r in new_records if r.status == AttendanceStatus.PRESENT)
            new_late = sum(1 for r in new_records if r.status == AttendanceStatus.LATE)
            new_excused = sum(1 for r in new_records if r.status == AttendanceStatus.EXCUSED)
            new_absent = sum(1 for r in new_records if r.status == AttendanceStatus.ABSENT)
        
        # Оценки за лабы после перевода
        new_grades_query = (
            select(LessonGrade)
            .join(Lesson, LessonGrade.lesson_id == Lesson.id)
            .where(
                LessonGrade.student_id == student.id,
                Lesson.date > transfer.transfer_date
            )
        )
        if att_settings.period_end_date:
            new_grades_query = new_grades_query.where(Lesson.date <= att_settings.period_end_date)
        
        new_grades_result = await self.db.execute(new_grades_query)
        new_grades = list(new_grades_result.scalars().all())
        
        # Merge оценок: берём лучшую оценку (старую или новую)
        all_grades = dict(old_lab_grades)
        for g in new_grades:
            if g.work_number is not None:
                old_grade = all_grades.get(g.work_number, 0)
                all_grades[g.work_number] = max(old_grade, g.grade)
        
        # Активность после перевода
        new_activity_query = select(func.sum(Activity.points)).where(
            Activity.student_id == student.id,
            Activity.attestation_type == attestation_type,
            Activity.is_active == True,
            Activity.created_at > transfer.created_at
        )
        new_activity_result = await self.db.execute(new_activity_query)
        new_activity = new_activity_result.scalar() or 0.0
        
        # === ОБЪЕДИНЕНИЕ ===
        total_lessons = old_total_lessons + len(new_lessons)
        total_present = old_present + new_present
        total_late = old_late + new_late
        total_excused = old_excused + new_excused
        total_absent = old_absent + new_absent
        total_activity_points = old_activity + new_activity + activity_points
        
        # Расчёт лаб
        labs_count = len(all_grades)
        labs_sum = sum(all_grades.values())
        labs_avg = labs_sum / labs_count if labs_count > 0 else 0
        
        lab_result = LabScoreResult(
            raw_score=labs_avg,
            weighted_score=labs_avg * att_settings.labs_weight / 100,
            labs_count=labs_count,
            required_count=att_settings.required_labs_count,
            bonus_points=max(0, labs_count - att_settings.required_labs_count) * att_settings.bonus_per_extra_lab
        )
        
        # Расчёт посещаемости
        att_raw = (
            total_present * att_settings.present_points +
            total_late * att_settings.late_points +
            total_excused * att_settings.excused_points +
            total_absent * att_settings.absent_points
        )
        att_max = total_lessons * att_settings.present_points if total_lessons > 0 else 1
        att_ratio = att_raw / att_max if att_max > 0 else 0
        
        attendance_result_calc = AttendanceScoreResult(
            raw_score=att_ratio * 100,
            weighted_score=att_ratio * att_settings.attendance_weight,
            total_classes=total_lessons,
            present_count=total_present,
            late_count=total_late,
            excused_count=total_excused,
            absent_count=total_absent
        )
        
        # Расчёт активности
        activity_score = self.calculator.calculate_activity_score(total_activity_points, att_settings)
        
        # Итоговый расчёт
        total_score, grade, is_passing = self.calculator.calculate_total_score(
            lab_result, attendance_result_calc, activity_score, att_settings
        )
        
        breakdown = ComponentBreakdown(
            labs_raw_score=lab_result.raw_score,
            labs_weighted_score=lab_result.weighted_score,
            labs_count=lab_result.labs_count,
            labs_required=lab_result.required_count,
            labs_bonus=lab_result.bonus_points,
            attendance_raw_score=attendance_result_calc.raw_score,
            attendance_weighted_score=attendance_result_calc.weighted_score,
            attendance_total_classes=attendance_result_calc.total_classes,
            attendance_present=attendance_result_calc.present_count,
            attendance_late=attendance_result_calc.late_count,
            attendance_excused=attendance_result_calc.excused_count,
            attendance_absent=attendance_result_calc.absent_count,
            activity_raw_score=total_activity_points,
            activity_weighted_score=activity_score
        )
        
        return AttestationResult(
            student_id=student.id,
            student_name=student.full_name or str(student.id),
            attestation_type=attestation_type,
            total_score=round(total_score, 2),
            lab_score=round(lab_result.weighted_score, 2),
            attendance_score=round(attendance_result_calc.weighted_score, 2),
            activity_score=round(activity_score, 2),
            grade=grade,
            is_passing=is_passing,
            max_points=AttestationSettings.get_max_points(attestation_type),
            min_passing_points=AttestationSettings.get_min_passing_points(attestation_type),
            components_breakdown=breakdown
        )
