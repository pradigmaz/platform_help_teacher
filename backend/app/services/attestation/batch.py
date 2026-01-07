"""
Модуль пакетных операций расчёта баллов.
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
    
    async def calculate_all_students(
        self,
        attestation_type: AttestationType
    ) -> tuple[List[AttestationResult], List[CalculationErrorInfo]]:
        """
        Расчёт баллов для ВСЕХ студентов (все группы).
        Сортировка по ФИО (А-Я).
        
        Использует snapshot настроек в начале для консистентности расчётов.
        """
        # SNAPSHOT: Получаем настройки один раз в начале для всех групп
        # Это предотвращает race condition если настройки изменятся во время расчёта
        att_settings = await self.settings_manager.get_or_create_settings(attestation_type)
        
        # 1. Получаем все группы
        groups_query = select(Group)
        groups_result = await self.db.execute(groups_query)
        groups = list(groups_result.scalars().all())
        
        if not groups:
            return [], []
        
        group_codes = {g.id: g.code for g in groups}
        
        # 2. Получаем всех студентов из всех групп
        students_query = select(User).where(
            User.role == UserRole.STUDENT,
            User.is_active == True,
            User.group_id.isnot(None)
        )
        students_result = await self.db.execute(students_query)
        all_students = list(students_result.scalars().all())
        
        if not all_students:
            return [], []
        
        # Группируем студентов по группам
        students_by_group = defaultdict(list)
        for student in all_students:
            students_by_group[student.group_id].append(student)
        
        # 3. Рассчитываем баллы для каждой группы с тем же snapshot настроек
        all_results = []
        all_errors = []
        
        for group_id, students in students_by_group.items():
            group_code = group_codes.get(group_id, "")
            
            # Передаём snapshot настроек вместо повторного запроса
            results, errors = await self._calculate_group_batch_with_settings(
                group_id=group_id,
                attestation_type=attestation_type,
                students=students,
                att_settings=att_settings  # Используем snapshot
            )
            
            for result in results:
                result.group_code = group_code
            
            all_results.extend(results)
            all_errors.extend(errors)
        
        # 4. Сортируем по ФИО (А-Я)
        all_results.sort(key=lambda x: x.student_name.lower())
        
        return all_results, all_errors

    async def calculate_group_batch(
        self,
        group_id: UUID,
        attestation_type: AttestationType,
        students: Optional[List[User]] = None
    ) -> tuple[List[AttestationResult], List[CalculationErrorInfo]]:
        """
        Пакетный расчёт баллов для группы.
        Optimized to avoid N+1 queries.
        """
        att_settings = await self.settings_manager.get_or_create_settings(attestation_type)
        return await self._calculate_group_batch_with_settings(
            group_id, attestation_type, students, att_settings
        )

    async def _calculate_group_batch_with_settings(
        self,
        group_id: UUID,
        attestation_type: AttestationType,
        students: Optional[List[User]],
        att_settings: AttestationSettings
    ) -> tuple[List[AttestationResult], List[CalculationErrorInfo]]:
        """
        Внутренний метод расчёта с переданными настройками.
        Используется для предотвращения race condition при batch операциях.
        """
        
        # Получаем студентов если не переданы
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
            
        student_ids = [s.id for s in students]
        
        # Получаем ВСЕ занятия группы за период
        all_lessons_query = select(Lesson).where(Lesson.group_id == group_id)
        if att_settings.period_start_date:
            all_lessons_query = all_lessons_query.where(Lesson.date >= att_settings.period_start_date)
        if att_settings.period_end_date:
            all_lessons_query = all_lessons_query.where(Lesson.date <= att_settings.period_end_date)
        
        all_lessons_result = await self.db.execute(all_lessons_query)
        all_lessons = list(all_lessons_result.scalars().all())
        
        # Группируем занятия по подгруппам
        lessons_by_subgroup = defaultdict(list)
        for lesson in all_lessons:
            lessons_by_subgroup[lesson.subgroup].append(lesson)
        
        # Batch: все оценки за лабы
        lesson_grades_query = (
            select(LessonGrade)
            .join(Lesson, LessonGrade.lesson_id == Lesson.id)
            .where(LessonGrade.student_id.in_(student_ids))
        )
        if att_settings.period_start_date:
            lesson_grades_query = lesson_grades_query.where(Lesson.date >= att_settings.period_start_date)
        if att_settings.period_end_date:
            lesson_grades_query = lesson_grades_query.where(Lesson.date <= att_settings.period_end_date)
        
        lesson_grades_result = await self.db.execute(lesson_grades_query)
        all_lesson_grades = lesson_grades_result.scalars().all()
        
        lesson_grades_by_student = defaultdict(list)
        for lg in all_lesson_grades:
            lesson_grades_by_student[lg.student_id].append(lg)
            
        # Batch: вся посещаемость
        attendance_query = select(Attendance).where(
            Attendance.group_id == group_id,
            Attendance.student_id.in_(student_ids)
        )
        
        attendance_result = await self.db.execute(attendance_query)
        all_attendance = attendance_result.scalars().all()
        
        attendance_by_student = defaultdict(list)
        for a in all_attendance:
            attendance_by_student[a.student_id].append(a)
            
        # Batch: баллы активности
        activity_query = select(Activity.student_id, func.sum(Activity.points)).where(
            Activity.student_id.in_(student_ids),
            Activity.attestation_type == attestation_type,
            Activity.is_active == True
        ).group_by(Activity.student_id)
        
        activity_result = await self.db.execute(activity_query)
        activity_map = {row[0]: row[1] for row in activity_result.all()}
            
        # Рассчитываем баллы для каждого студента
        results = []
        errors = []
        
        for student in students:
            student_lesson_grades = lesson_grades_by_student.get(student.id, [])
            activity_points = activity_map.get(student.id, 0.0)
            student_name = student.full_name or str(student.id)
            
            # Определяем релевантные занятия для подгруппы студента
            student_subgroup = student.subgroup
            if student_subgroup is not None:
                relevant_lessons = lessons_by_subgroup[None] + lessons_by_subgroup[student_subgroup]
            else:
                relevant_lessons = lessons_by_subgroup[None]
            
            relevant_dates = {l.date for l in relevant_lessons}
            
            # Фильтруем посещаемость по релевантным датам
            all_student_attendance = attendance_by_student.get(student.id, [])
            student_attendance = [a for a in all_student_attendance if a.date in relevant_dates]
            
            try:
                lab_result = self.calculator.calculate_lesson_grades_score(student_lesson_grades, att_settings)
                attendance_result_calc = self.calculator.calculate_attendance_score(student_attendance, att_settings)
                activity_score = self.calculator.calculate_activity_score(activity_points, att_settings)
                
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
                    activity_raw_score=activity_points,
                    activity_weighted_score=activity_score
                )
                
                results.append(AttestationResult(
                    student_id=student.id,
                    student_name=student_name,
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
                ))
            except (ValueError, TypeError, AttributeError, ZeroDivisionError) as e:
                logger.error(f"Error calculating score for student {student.id}: {e}")
                errors.append(CalculationErrorInfo(
                    student_id=student.id,
                    student_name=student_name,
                    error=str(e)
                ))
                continue
                
        return results, errors
