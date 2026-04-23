"""
Расчёт баллов для одного студента (автобалансировка).
"""

import logging
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.attendance import Attendance
from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.lesson import Lesson
from app.models.lesson_grade import LessonGrade
from app.models.schedule import LessonType
from app.models.student_transfer import StudentTransfer
from app.models.user import User
from app.schemas.attestation import AttestationResult, ComponentBreakdown
from app.services.attendance_period import (
    calculate_expected_lessons,
    filter_attendance_records_to_lessons,
    get_relevant_lessons_for_subgroup,
    group_lessons_by_subgroup,
    load_attendance_by_student_for_lessons,
    load_period_lessons,
)
from app.services.offering_policy_resolver import resolve_offering_policy_for_group_subject

from .calculator import AttestationCalculator
from .lab_progress import dedupe_lesson_grade_rows, dedupe_transfer_lab_grades
from .settings import AttestationSettingsManager
from .subject_scope import (
    AttestationSubjectScope,
    merge_transfer_attendance,
    merge_transfer_lab_grades,
    resolve_attestation_subject_scope,
    sum_transfer_activity_points,
)
from .submission_fallbacks import get_student_submission_grade_fallbacks

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
        extra_activity_points: float = 0.0,
        subject_id: UUID | None = None,
    ) -> AttestationResult:
        """Расчёт баллов аттестации для студента."""
        settings = await self.settings_manager.get_or_create_settings(attestation_type)
        subject_scope = await resolve_attestation_subject_scope(
            self.db,
            group_id=group_id,
            settings=settings,
            requested_subject_id=subject_id,
        )
        policy = await resolve_offering_policy_for_group_subject(
            self.db,
            group_id=group_id,
            subject_id=subject_scope.subject_id,
            settings=settings,
        )

        student = await self._get_student(student_id)
        if not student:
            raise ValueError(f"Студент {student_id} не найден")

        lesson_grades = await self._get_lesson_grades(student_id, group_id, settings, subject_scope.subject_id)
        submission_grades = await get_student_submission_grade_fallbacks(
            self.db,
            student_id,
            group_id,
            settings,
            subject_id=subject_scope.subject_id,
        )
        attendance_records = await self._get_attendance(
            student_id,
            group_id,
            student.subgroup,
            settings,
            subject_scope.subject_id,
        )
        db_activity_points = await self._get_activity_points(student_id, attestation_type, subject_scope)

        transfers = await self._get_transfers_in_period(student_id, attestation_type, settings)
        transfer_attendance = merge_transfer_attendance(transfers, subject_scope)
        transfer_lab_grades = dedupe_transfer_lab_grades(merge_transfer_lab_grades(transfers, subject_scope))
        transfer_activity = sum_transfer_activity_points(transfers, subject_scope)

        expected_lessons = await self._get_expected_lessons(
            group_id,
            student.subgroup,
            settings,
            subject_scope.subject_id,
        )

        lab_result = self.calculator.calculate_labs(
            lesson_grades,
            settings,
            transfer_lab_grades,
            submission_grades,
            labs_required_override=policy.labs_required_for(attestation_type),
        )
        attendance_result = self.calculator.calculate_attendance(
            attendance_records,
            settings,
            expected_lessons,
            transfer_attendance,
        )

        current_score = lab_result.score + attendance_result.score
        total_activity = db_activity_points + extra_activity_points + transfer_activity
        activity_score, bonus_blocked = self.calculator.calculate_activity(total_activity, current_score, settings)

        total_score, grade, is_passing = self.calculator.calculate_total(
            lab_result,
            attendance_result,
            activity_score,
            settings,
        )

        breakdown = ComponentBreakdown(
            labs_score=lab_result.score,
            labs_count=lab_result.labs_count,
            labs_required=lab_result.labs_required,
            labs_max=lab_result.max_score,
            attendance_score=attendance_result.score,
            attendance_ratio=attendance_result.ratio,
            attendance_max=attendance_result.max_score,
            total_classes=attendance_result.total_classes,
            expected_lessons=attendance_result.expected_lessons,
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
            subject_id=subject_scope.subject_id,
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
        self,
        student_id: UUID,
        group_id: UUID,
        settings: AttestationSettings,
        subject_id: UUID | None = None,
    ) -> list[LessonGrade]:
        period_start, period_end = settings.get_effective_period()
        query = (
            select(LessonGrade, Lesson.subject_id)
            .join(Lesson, LessonGrade.lesson_id == Lesson.id)
            .where(LessonGrade.student_id == student_id)
            .where(LessonGrade.work_number.isnot(None))
            .where(Lesson.group_id == group_id)
            .where(Lesson.lesson_type.in_((LessonType.LAB, LessonType.PRACTICE)))
            .where(Lesson.is_cancelled.is_(False))
            .where(Lesson.date >= period_start)
            .where(Lesson.date <= period_end)
        )
        if subject_id:
            query = query.where(Lesson.subject_id == subject_id)
        result = await self.db.execute(query)
        return dedupe_lesson_grade_rows(result.all())

    async def _get_attendance(
        self,
        student_id: UUID,
        group_id: UUID,
        subgroup: int | None,
        settings: AttestationSettings,
        subject_id: UUID | None = None,
    ) -> list[Attendance]:
        period_start, period_end = settings.get_effective_period()
        lessons = await load_period_lessons(
            self.db,
            group_id=group_id,
            period_start=period_start,
            period_end=period_end,
            subject_id=subject_id,
        )
        lessons_by_subgroup = group_lessons_by_subgroup(lessons)
        relevant_lessons = get_relevant_lessons_for_subgroup(lessons_by_subgroup, subgroup)
        if not relevant_lessons:
            return []

        attendance_by_student = await load_attendance_by_student_for_lessons(
            self.db,
            group_id=group_id,
            student_ids=[student_id],
            lessons=relevant_lessons,
        )
        return filter_attendance_records_to_lessons(attendance_by_student.get(student_id, []), relevant_lessons)

    async def _get_activity_points(
        self,
        student_id: UUID,
        attestation_type: AttestationType,
        subject_scope: AttestationSubjectScope,
    ) -> float:
        query = select(func.sum(Activity.points)).where(
            Activity.student_id == student_id,
            Activity.attestation_type == attestation_type,
            Activity.is_active,
        )
        if subject_scope.subject_id is not None:
            if subject_scope.can_use_legacy_activity_points:
                query = query.where(
                    or_(
                        Activity.subject_id == subject_scope.subject_id,
                        Activity.subject_id.is_(None),
                    )
                )
            else:
                query = query.where(Activity.subject_id == subject_scope.subject_id)

        result = await self.db.execute(query)
        return result.scalar() or 0.0

    async def _get_expected_lessons(
        self,
        group_id: UUID,
        subgroup: int | None,
        settings: AttestationSettings,
        subject_id: UUID | None = None,
    ) -> int:
        """Получить ожидаемое количество занятий."""
        period_start, period_end = settings.get_effective_period()
        lessons = await load_period_lessons(
            self.db,
            group_id=group_id,
            period_start=period_start,
            period_end=period_end,
            subject_id=subject_id,
        )
        lessons_by_subgroup = group_lessons_by_subgroup(lessons)
        relevant_lessons = get_relevant_lessons_for_subgroup(lessons_by_subgroup, subgroup)
        return calculate_expected_lessons(relevant_lessons, minimum=settings.get_min_expected_lessons())

    async def _get_transfers_in_period(
        self,
        student_id: UUID,
        attestation_type: AttestationType,
        settings: AttestationSettings,
    ) -> list[StudentTransfer]:
        """Получить переводы студента в периоде аттестации."""
        period_start, period_end = settings.get_effective_period()
        query = (
            select(StudentTransfer)
            .where(StudentTransfer.student_id == student_id)
            .where(StudentTransfer.attestation_type == attestation_type)
            .where(StudentTransfer.transfer_date >= period_start)
            .where(StudentTransfer.transfer_date <= period_end)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
