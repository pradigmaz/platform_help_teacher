"""Пакетные операции расчёта баллов (автобалансировка)."""

import logging
from collections import defaultdict
from time import perf_counter
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserRole
from app.models.activity import Activity
from app.models.attendance import Attendance
from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.lesson import Lesson
from app.models.lesson_grade import LessonGrade
from app.models.student_transfer import StudentTransfer
from app.models.user import User
from app.schemas.attestation import AttestationResult, CalculationErrorInfo, ComponentBreakdown
from app.services.attendance_slots import build_attendance_slot_filter, get_lesson_slot_sets, matches_attendance_slot

from .calculator import AttestationCalculator
from .lab_progress import dedupe_lesson_grade_rows, dedupe_transfer_lab_grades
from .settings import AttestationSettingsManager
from .subject_scope import (
    AttestationSubjectScope,
    apply_lab_lesson_type_scope,
    apply_lesson_subject_scope,
    merge_transfer_attendance,
    merge_transfer_lab_grades,
    resolve_attestation_subject_scope,
    sum_transfer_activity_points,
)
from .submission_fallbacks import get_submission_grade_fallbacks_batch

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
        students: list[User] | None = None,
        subject_id: UUID | None = None,
    ) -> tuple[list[AttestationResult], list[CalculationErrorInfo]]:
        total_started_at = perf_counter()
        settings = await self.settings_manager.get_or_create_settings(attestation_type)
        settings_loaded_at = perf_counter()
        subject_scope = await resolve_attestation_subject_scope(
            self.db,
            group_id=group_id,
            settings=settings,
            requested_subject_id=subject_id,
        )
        subject_scope_at = perf_counter()

        if not students:
            students_query = select(User).where(
                User.group_id == group_id,
                User.role == UserRole.STUDENT,
                User.is_active,
            )
            students_result = await self.db.execute(students_query)
            students = list(students_result.scalars().all())
        if not students:
            return [], []
        students_loaded_at = perf_counter()
        student_ids = [student.id for student in students]
        lessons = await self._get_lessons(group_id, settings, subject_scope.subject_id)
        lessons_loaded_at = perf_counter()
        lessons_by_subgroup = self._group_lessons_by_subgroup(lessons)
        lesson_grades_map = await self._get_lesson_grades_batch(
            student_ids, group_id, settings, subject_scope.subject_id
        )
        grades_loaded_at = perf_counter()
        submission_grades_map = await get_submission_grade_fallbacks_batch(
            self.db,
            student_ids,
            group_id,
            settings,
            subject_id=subject_scope.subject_id,
        )
        submission_fallbacks_at = perf_counter()
        attendance_map = await self._get_attendance_batch(group_id, student_ids, settings, lessons)
        attendance_loaded_at = perf_counter()
        activity_map = await self._get_activity_batch(student_ids, attestation_type, subject_scope)
        activity_loaded_at = perf_counter()
        transfers_map = await self._get_transfers_batch(student_ids, attestation_type, settings)
        transfers_loaded_at = perf_counter()

        results: list[AttestationResult] = []
        errors: list[CalculationErrorInfo] = []
        for student in students:
            try:
                results.append(
                    self._calculate_student(
                        student,
                        settings,
                        lessons_by_subgroup,
                        lesson_grades_map,
                        submission_grades_map,
                        attendance_map,
                        activity_map,
                        transfers_map,
                        subject_scope,
                    )
                )
            except Exception as exc:
                logger.error("Error for student %s: %s", student.id, exc)
                errors.append(
                    CalculationErrorInfo(
                        student_id=student.id,
                        student_name=student.full_name or str(student.id),
                        error=str(exc),
                    )
                )
        calculated_at = perf_counter()

        logger.info(
            "attestation.batch_timing group=%s type=%s students=%s settings=%.4fs scope=%.4fs students_q=%.4fs "
            "lessons=%.4fs grades=%.4fs submission_fallbacks=%.4fs attendance=%.4fs activity=%.4fs "
            "transfers=%.4fs calculate=%.4fs total=%.4fs",
            group_id,
            attestation_type,
            len(students),
            settings_loaded_at - total_started_at,
            subject_scope_at - settings_loaded_at,
            students_loaded_at - subject_scope_at,
            lessons_loaded_at - students_loaded_at,
            grades_loaded_at - lessons_loaded_at,
            submission_fallbacks_at - grades_loaded_at,
            attendance_loaded_at - submission_fallbacks_at,
            activity_loaded_at - attendance_loaded_at,
            transfers_loaded_at - activity_loaded_at,
            calculated_at - transfers_loaded_at,
            calculated_at - total_started_at,
        )

        return results, errors

    def _calculate_student(
        self,
        student: User,
        settings: AttestationSettings,
        lessons_by_subgroup: dict[int | None, list[Lesson]],
        lesson_grades_map: dict[UUID, list[LessonGrade]],
        submission_grades_map: dict[UUID, list[dict]],
        attendance_map: dict[UUID, list[Attendance]],
        activity_map: dict[UUID, float],
        transfers_map: dict[UUID, list[StudentTransfer]],
        subject_scope: AttestationSubjectScope,
    ) -> AttestationResult:
        subgroup = student.subgroup
        if subgroup is not None:
            relevant_lessons = lessons_by_subgroup.get(None, []) + lessons_by_subgroup.get(subgroup, [])
        else:
            relevant_lessons = lessons_by_subgroup.get(None, [])
        lesson_ids, legacy_slots = get_lesson_slot_sets(relevant_lessons)
        expected_lessons = max(len(relevant_lessons), settings.get_min_expected_lessons())

        all_attendance = attendance_map.get(student.id, [])
        attendance = [
            record
            for record in all_attendance
            if matches_attendance_slot(record, lesson_ids=lesson_ids, legacy_slots=legacy_slots)
        ]
        student_transfers = transfers_map.get(student.id, [])
        transfer_attendance = merge_transfer_attendance(student_transfers, subject_scope)
        transfer_lab_grades = dedupe_transfer_lab_grades(merge_transfer_lab_grades(student_transfers, subject_scope))
        transfer_activity = sum_transfer_activity_points(student_transfers, subject_scope)
        lab_result = self.calculator.calculate_labs(
            lesson_grades_map.get(student.id, []),
            settings,
            transfer_lab_grades,
            submission_grades_map.get(student.id, []),
        )
        attendance_result = self.calculator.calculate_attendance(
            attendance,
            settings,
            expected_lessons,
            transfer_attendance,
        )
        current_score = lab_result.score + attendance_result.score
        total_activity = activity_map.get(student.id, 0.0) + transfer_activity
        activity_score, bonus_blocked = self.calculator.calculate_activity(total_activity, current_score, settings)
        total_score, grade, is_passing = self.calculator.calculate_total(
            lab_result,
            attendance_result,
            activity_score,
            settings,
        )
        return AttestationResult(
            student_id=student.id,
            student_name=student.full_name or str(student.id),
            attestation_type=settings.attestation_type,
            subject_id=subject_scope.subject_id,
            total_score=total_score,
            grade=grade,
            is_passing=is_passing,
            max_points=settings.attestation_type.max_points,
            min_passing_points=AttestationSettings.get_min_passing_points(settings.attestation_type),
            breakdown=ComponentBreakdown(
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
            ),
        )

    async def _get_lessons(
        self,
        group_id: UUID,
        settings: AttestationSettings,
        subject_id: UUID | None,
    ) -> list[Lesson]:
        period_start, period_end = settings.get_effective_period()
        query = (
            select(Lesson)
            .where(Lesson.group_id == group_id)
            .where(Lesson.is_cancelled.is_(False))
            .where(Lesson.date >= period_start)
            .where(Lesson.date <= period_end)
        )
        query = apply_lesson_subject_scope(query, subject_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _group_lessons_by_subgroup(self, lessons: list[Lesson]) -> dict[int | None, list[Lesson]]:
        grouped: dict[int | None, list[Lesson]] = defaultdict(list)
        for lesson in lessons:
            grouped[lesson.subgroup].append(lesson)
        return grouped

    async def _get_lesson_grades_batch(
        self,
        student_ids: list[UUID],
        group_id: UUID,
        settings: AttestationSettings,
        subject_id: UUID | None,
    ) -> dict[UUID, list[LessonGrade]]:
        period_start, period_end = settings.get_effective_period()
        query = (
            select(LessonGrade, Lesson.subject_id)
            .join(Lesson, LessonGrade.lesson_id == Lesson.id)
            .where(LessonGrade.student_id.in_(student_ids))
            .where(LessonGrade.work_number.isnot(None))
            .where(Lesson.group_id == group_id)
            .where(Lesson.is_cancelled.is_(False))
            .where(Lesson.date >= period_start)
            .where(Lesson.date <= period_end)
        )
        query = apply_lab_lesson_type_scope(apply_lesson_subject_scope(query, subject_id))
        result = await self.db.execute(query)
        rows_by_student: dict[UUID, list[tuple[LessonGrade, UUID | None]]] = defaultdict(list)
        for grade, grade_subject_id in result.all():
            rows_by_student[grade.student_id].append((grade, grade_subject_id))
        return {student_id: dedupe_lesson_grade_rows(rows) for student_id, rows in rows_by_student.items()}

    async def _get_attendance_batch(
        self,
        group_id: UUID,
        student_ids: list[UUID],
        settings: AttestationSettings,
        lessons: list[Lesson],
    ) -> dict[UUID, list[Attendance]]:
        if not lessons:
            return {}
        slot_filter = build_attendance_slot_filter(lessons)
        query = select(Attendance).where(
            Attendance.group_id == group_id,
            Attendance.student_id.in_(student_ids),
            slot_filter,
        )
        result = await self.db.execute(query)
        grouped: dict[UUID, list[Attendance]] = defaultdict(list)
        for record in result.scalars().all():
            grouped[record.student_id].append(record)
        return grouped

    async def _get_activity_batch(
        self,
        student_ids: list[UUID],
        attestation_type: AttestationType,
        subject_scope: AttestationSubjectScope,
    ) -> dict[UUID, float]:
        query = (
            select(Activity.student_id, func.sum(Activity.points))
            .where(
                Activity.student_id.in_(student_ids),
                Activity.attestation_type == attestation_type,
                Activity.is_active,
            )
            .group_by(Activity.student_id)
        )
        if subject_scope.subject_id is not None:
            if subject_scope.can_use_legacy_activity_points:
                query = query.where(or_(Activity.subject_id == subject_scope.subject_id, Activity.subject_id.is_(None)))
            else:
                query = query.where(Activity.subject_id == subject_scope.subject_id)
        result = await self.db.execute(query)
        return {student_id: points or 0.0 for student_id, points in result.all()}

    async def _get_transfers_batch(
        self,
        student_ids: list[UUID],
        attestation_type: AttestationType,
        settings: AttestationSettings,
    ) -> dict[UUID, list[StudentTransfer]]:
        period_start, period_end = settings.get_effective_period()
        query = (
            select(StudentTransfer)
            .where(StudentTransfer.student_id.in_(student_ids))
            .where(StudentTransfer.attestation_type == attestation_type)
            .where(StudentTransfer.transfer_date >= period_start)
            .where(StudentTransfer.transfer_date <= period_end)
        )
        result = await self.db.execute(query)
        grouped: dict[UUID, list[StudentTransfer]] = defaultdict(list)
        for transfer in result.scalars().all():
            grouped[transfer.student_id].append(transfer)
        return grouped
