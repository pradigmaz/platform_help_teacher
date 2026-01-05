"""
Сервис для управления настройками аттестации и расчёта баллов.

Реализует Requirements 5.1, 5.2 - API для получения и обновления настроек.
Реализует Requirements 6.1-6.3 - расчёт баллов для студентов и групп.
"""
import logging
from typing import Optional, List
from uuid import UUID
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.attendance import Attendance
from app.models.submission import Submission
from app.models.lab import Lab
from app.models.user import User
from app.models.activity import Activity
from app.schemas.attestation import (
    AttestationSettingsUpdate,
    AttestationSettingsResponse,
    AttestationResult,
    ComponentBreakdown,
    CalculationErrorInfo,
)

from .calculator import AttestationCalculator

logger = logging.getLogger(__name__)


class AttestationService:
    """
    Сервис для работы с настройками аттестации и расчётом баллов.
    
    Методы:
    - get_settings: получение настроек для типа аттестации
    - update_settings: обновление настроек аттестации
    - get_or_create_settings: получение или создание настроек по умолчанию
    - calculate_student_score: расчёт баллов для студента
    - calculate_group_scores_batch: пакетный расчёт баллов для группы
    - calculate_all_students_scores: расчёт баллов для всех студентов
    """
    
    # Значения по умолчанию для настроек (Requirements 1.7-1.11)
    DEFAULT_SETTINGS = {
        'labs_weight': settings.ATTESTATION_DEFAULT_LABS_WEIGHT,
        'attendance_weight': settings.ATTESTATION_DEFAULT_ATTENDANCE_WEIGHT,
        'activity_weight': settings.ATTESTATION_DEFAULT_ACTIVITY_WEIGHT,
        'required_labs_count': settings.ATTESTATION_DEFAULT_REQUIRED_LABS_COUNT,
        'bonus_per_extra_lab': settings.ATTESTATION_DEFAULT_BONUS_PER_EXTRA_LAB,
        'soft_deadline_penalty': settings.ATTESTATION_DEFAULT_SOFT_DEADLINE_PENALTY,
        'hard_deadline_penalty': settings.ATTESTATION_DEFAULT_HARD_DEADLINE_PENALTY,
        'soft_deadline_days': settings.ATTESTATION_DEFAULT_SOFT_DEADLINE_DAYS,
        'present_points': settings.ATTESTATION_DEFAULT_PRESENT_POINTS,
        'late_points': settings.ATTESTATION_DEFAULT_LATE_POINTS,
        'excused_points': settings.ATTESTATION_DEFAULT_EXCUSED_POINTS,
        'absent_points': settings.ATTESTATION_DEFAULT_ABSENT_POINTS,
        'activity_enabled': settings.ATTESTATION_DEFAULT_ACTIVITY_ENABLED,
        'participation_points': settings.ATTESTATION_DEFAULT_PARTICIPATION_POINTS,
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.calculator = AttestationCalculator()
    
    # ==================== Settings Methods ====================
    
    async def get_settings(
        self,
        attestation_type: AttestationType
    ) -> Optional[AttestationSettings]:
        """Получение глобальных настроек аттестации."""
        query = select(AttestationSettings).where(
            AttestationSettings.attestation_type == attestation_type
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_or_create_settings(
        self,
        attestation_type: AttestationType
    ) -> AttestationSettings:
        """Получение настроек или создание с значениями по умолчанию."""
        att_settings = await self.get_settings(attestation_type)
        
        if att_settings is None:
            att_settings = await self.create_default_settings(attestation_type)
        
        return att_settings
    
    async def create_default_settings(
        self,
        attestation_type: AttestationType
    ) -> AttestationSettings:
        """Создание глобальных настроек по умолчанию для типа аттестации."""
        logger.info(f"Creating default global settings for type {attestation_type}")
        
        att_settings = AttestationSettings(
            attestation_type=attestation_type,
            labs_weight=self.DEFAULT_SETTINGS['labs_weight'],
            attendance_weight=self.DEFAULT_SETTINGS['attendance_weight'],
            activity_weight=self.DEFAULT_SETTINGS['activity_weight'],
            required_labs_count=self.DEFAULT_SETTINGS['required_labs_count'],
            bonus_per_extra_lab=self.DEFAULT_SETTINGS['bonus_per_extra_lab'],
            soft_deadline_penalty=self.DEFAULT_SETTINGS['soft_deadline_penalty'],
            hard_deadline_penalty=self.DEFAULT_SETTINGS['hard_deadline_penalty'],
            soft_deadline_days=self.DEFAULT_SETTINGS['soft_deadline_days'],
            present_points=self.DEFAULT_SETTINGS['present_points'],
            late_points=self.DEFAULT_SETTINGS['late_points'],
            excused_points=self.DEFAULT_SETTINGS['excused_points'],
            absent_points=self.DEFAULT_SETTINGS['absent_points'],
            activity_enabled=self.DEFAULT_SETTINGS['activity_enabled'],
            participation_points=self.DEFAULT_SETTINGS['participation_points'],
        )
        
        self.db.add(att_settings)
        await self.db.commit()
        await self.db.refresh(att_settings)
        
        return att_settings
    
    async def initialize_settings(
        self
    ) -> tuple[AttestationSettings, AttestationSettings]:
        """Инициализация глобальных настроек аттестации для обоих типов."""
        logger.info("Initializing global attestation settings")
        
        first_settings = await self.get_or_create_settings(AttestationType.FIRST)
        second_settings = await self.get_or_create_settings(AttestationType.SECOND)
        
        return first_settings, second_settings
    
    async def update_settings(
        self,
        settings_update: AttestationSettingsUpdate
    ) -> AttestationSettings:
        """Обновление глобальных настроек аттестации."""
        att_settings = await self.get_or_create_settings(settings_update.attestation_type)
        
        update_data = settings_update.model_dump(exclude={'attestation_type'})
        for field, value in update_data.items():
            setattr(att_settings, field, value)
        
        if not att_settings.validate_weights():
            raise ValueError(
                f"Веса компонентов должны суммироваться в 100%. "
                f"Текущая сумма: {att_settings.labs_weight + att_settings.attendance_weight + att_settings.activity_weight}%"
            )
        
        await self.db.commit()
        await self.db.refresh(att_settings)
        
        logger.info(f"Updated global attestation settings for type {settings_update.attestation_type}")
        return att_settings
    
    def to_response(self, att_settings: AttestationSettings) -> AttestationSettingsResponse:
        """Преобразование модели в схему ответа с вычисляемыми полями."""
        return AttestationSettingsResponse(
            id=att_settings.id,
            attestation_type=att_settings.attestation_type,
            labs_weight=att_settings.labs_weight,
            attendance_weight=att_settings.attendance_weight,
            activity_weight=att_settings.activity_weight,
            required_labs_count=att_settings.required_labs_count,
            bonus_per_extra_lab=att_settings.bonus_per_extra_lab,
            soft_deadline_penalty=att_settings.soft_deadline_penalty,
            hard_deadline_penalty=att_settings.hard_deadline_penalty,
            soft_deadline_days=att_settings.soft_deadline_days,
            present_points=att_settings.present_points,
            late_points=att_settings.late_points,
            excused_points=att_settings.excused_points,
            absent_points=att_settings.absent_points,
            activity_enabled=att_settings.activity_enabled,
            participation_points=att_settings.participation_points,
            components_config=att_settings.components_config,
            created_at=att_settings.created_at,
            updated_at=att_settings.updated_at,
            max_points=AttestationSettings.get_max_points(att_settings.attestation_type),
            min_passing_points=AttestationSettings.get_min_passing_points(att_settings.attestation_type),
            grade_scale=AttestationSettings.get_grade_scale(att_settings.attestation_type),
        )

    # ==================== Calculation Methods ====================

    async def calculate_student_score(
        self,
        student_id: UUID,
        group_id: UUID,
        attestation_type: AttestationType,
        activity_points: float = 0.0
    ) -> AttestationResult:
        """Расчёт баллов аттестации для студента."""
        att_settings = await self.get_or_create_settings(attestation_type)
        
        # Получаем данные студента
        student_query = select(User).where(User.id == student_id)
        student_result = await self.db.execute(student_query)
        student = student_result.scalar_one_or_none()
        
        if not student:
            raise ValueError(f"Студент с ID {student_id} не найден")
        
        # Получаем лабораторные работы
        labs_query = select(Lab)
        labs_result = await self.db.execute(labs_query)
        labs = list(labs_result.scalars().all())
        
        # Получаем сданные работы студента
        submissions_query = select(Submission).where(Submission.user_id == student_id)
        submissions_result = await self.db.execute(submissions_query)
        submissions = list(submissions_result.scalars().all())
        
        # Получаем записи посещаемости
        attendance_query = select(Attendance).where(
            Attendance.student_id == student_id,
            Attendance.group_id == group_id
        )
        attendance_result = await self.db.execute(attendance_query)
        attendance_records = list(attendance_result.scalars().all())
        
        # Получаем баллы за активность из БД
        db_activity_query = select(func.sum(Activity.points)).where(
            Activity.student_id == student_id,
            Activity.attestation_type == attestation_type,
            Activity.is_active == True
        )
        db_activity_result = await self.db.execute(db_activity_query)
        db_activity_points = db_activity_result.scalar() or 0.0
        
        total_activity_points = db_activity_points + activity_points
        
        # Расчёт компонентов
        lab_result = self.calculator.calculate_lab_score(submissions, labs, att_settings)
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
        
        student_name = student.full_name or str(student_id)
        
        return AttestationResult(
            student_id=student_id,
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
        )

    async def calculate_all_students_scores(
        self,
        attestation_type: AttestationType
    ) -> tuple[List[AttestationResult], List[CalculationErrorInfo]]:
        """
        Расчёт баллов для ВСЕХ студентов (все группы).
        Сортировка по ФИО (А-Я).
        """
        from app.models import UserRole
        from app.models.group import Group
        
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
        
        # 3. Рассчитываем баллы для каждой группы
        all_results = []
        all_errors = []
        
        for group_id, students in students_by_group.items():
            group_code = group_codes.get(group_id, "")
            
            results, errors = await self.calculate_group_scores_batch(
                group_id=group_id,
                attestation_type=attestation_type,
                students=students
            )
            
            for result in results:
                result.group_code = group_code
            
            all_results.extend(results)
            all_errors.extend(errors)
        
        # 4. Сортируем по ФИО (А-Я)
        all_results.sort(key=lambda x: x.student_name.lower())
        
        return all_results, all_errors

    async def calculate_group_scores_batch(
        self,
        group_id: UUID,
        attestation_type: AttestationType,
        students: Optional[List[User]] = None
    ) -> tuple[List[AttestationResult], List[CalculationErrorInfo]]:
        """
        Пакетный расчёт баллов для группы.
        Optimized to avoid N+1 queries.
        """
        att_settings = await self.get_or_create_settings(attestation_type)
        
        # Получаем лабораторные работы
        labs_query = select(Lab)
        labs_result = await self.db.execute(labs_query)
        labs = list(labs_result.scalars().all())
        
        # Получаем студентов если не переданы
        if not students:
            from app.models import UserRole
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
        
        # Batch: все сданные работы
        submissions_query = select(Submission).where(Submission.user_id.in_(student_ids))
        submissions_result = await self.db.execute(submissions_query)
        all_submissions = submissions_result.scalars().all()
        
        submissions_by_student = defaultdict(list)
        for s in all_submissions:
            submissions_by_student[s.user_id].append(s)
            
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
            student_submissions = submissions_by_student.get(student.id, [])
            student_attendance = attendance_by_student.get(student.id, [])
            activity_points = activity_map.get(student.id, 0.0)
            student_name = student.full_name or str(student.id)
            
            try:
                lab_result = self.calculator.calculate_lab_score(student_submissions, labs, att_settings)
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
            except Exception as e:
                logger.error(f"Error calculating score for student {student.id}: {e}")
                errors.append(CalculationErrorInfo(
                    student_id=student.id,
                    student_name=student_name,
                    error=str(e)
                ))
                continue
                
        return results, errors
