"""Normalized lab progress service for public group reports."""

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attestation_settings import AttestationSettings
from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.lesson_grade import LessonGrade
from app.models.submission import Submission
from app.models.user import User
from app.schemas.report import LabProgress
from app.services.attestation.lab_calculator import LabScoreCalculator
from app.services.attestation.lab_progress import dedupe_lesson_grade_rows, is_completed_lab_grade
from app.services.attestation.subject_scope import (
    apply_lab_lesson_type_scope,
    apply_lesson_subject_scope,
    resolve_attestation_subject_scope,
)
from app.services.attestation.submission_fallbacks import get_submission_grade_fallbacks_batch
from app.services.offering_policy_resolver import resolve_offering_policy_for_group_subject

logger = logging.getLogger(__name__)


LabStatsMap = dict[str, int]


@dataclass(frozen=True)
class ReportLabState:
    grade: int | None
    is_completed: bool


def _rank_grade(grade: LessonGrade) -> tuple[int, str, str]:
    updated_at = getattr(grade, "updated_at", None) or getattr(grade, "created_at", None)
    updated_at_str = updated_at.isoformat() if updated_at else ""
    return (grade.grade, updated_at_str, str(grade.id))


def _rank_lab(lab: Lab, subject_id: UUID | None) -> tuple[int, int, str, str]:
    created_at = getattr(lab, "created_at", None)
    created_at_str = created_at.isoformat() if created_at else ""
    return (
        int(subject_id is not None and lab.subject_id == subject_id),
        int(lab.is_published),
        created_at_str,
        str(lab.id),
    )


async def _resolve_subject_id(
    db: AsyncSession,
    group_id: UUID,
    settings: AttestationSettings,
    requested_subject_id: UUID | None = None,
) -> tuple[bool, UUID | None]:
    if requested_subject_id is not None:
        return True, requested_subject_id
    try:
        scope = await resolve_attestation_subject_scope(db, group_id=group_id, settings=settings)
    except ValueError as exc:
        logger.warning("Report labs subject scope unresolved for group %s: %s", group_id, exc)
        return False, None
    return True, scope.subject_id


async def _load_completed_states_by_student(
    db: AsyncSession,
    group_id: UUID,
    student_ids: list[UUID],
    settings: AttestationSettings,
    subject_id: UUID | None,
) -> dict[UUID, dict[int, ReportLabState]]:
    if not student_ids:
        return {}

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
    result = await db.execute(query)

    lesson_grades_by_student: dict[UUID, list[tuple[LessonGrade, UUID | None]]] = defaultdict(list)
    for grade, grade_subject_id in result.all():
        lesson_grades_by_student[grade.student_id].append((grade, grade_subject_id))

    submission_fallbacks = await get_submission_grade_fallbacks_batch(
        db,
        student_ids,
        group_id,
        settings,
        subject_id=subject_id,
    )

    calculator = LabScoreCalculator()
    states: dict[UUID, dict[int, ReportLabState]] = {}
    for student_id in student_ids:
        lab_result = calculator.calculate(
            dedupe_lesson_grade_rows(lesson_grades_by_student.get(student_id, [])),
            settings,
            submission_grades=submission_fallbacks.get(student_id, []),
        )
        states[student_id] = {
            detail["work_number"]: ReportLabState(
                grade=detail["grade"],
                is_completed=is_completed_lab_grade(detail["grade"]),
            )
            for detail in lab_result.details
            if detail.get("work_number") is not None
        }
    return states


async def _load_lab_catalog_by_number(
    db: AsyncSession,
    total_labs: int,
    subject_id: UUID | None,
) -> dict[int, Lab]:
    query = (
        select(Lab)
        .where(Lab.deleted_at.is_(None))
        .where(Lab.number >= 1)
        .where(Lab.number <= total_labs)
        .order_by(Lab.number.asc(), Lab.created_at.desc())
    )
    if subject_id is not None:
        query = query.where(Lab.subject_id == subject_id)
    result = await db.execute(query)
    selected: dict[int, Lab] = {}
    for lab in result.scalars().all():
        current = selected.get(lab.number)
        if current is None or _rank_lab(lab, subject_id) > _rank_lab(current, subject_id):
            selected[lab.number] = lab
    return selected


async def _load_student_journal_grades(
    db: AsyncSession,
    group_id: UUID,
    student_id: UUID,
    settings: AttestationSettings,
    subject_id: UUID | None,
) -> dict[int, LessonGrade]:
    period_start, period_end = settings.get_effective_period()
    query = (
        select(LessonGrade, Lesson.subject_id)
        .join(Lesson, LessonGrade.lesson_id == Lesson.id)
        .where(LessonGrade.student_id == student_id)
        .where(LessonGrade.work_number.isnot(None))
        .where(Lesson.group_id == group_id)
        .where(Lesson.is_cancelled.is_(False))
        .where(Lesson.date >= period_start)
        .where(Lesson.date <= period_end)
    )
    query = apply_lab_lesson_type_scope(apply_lesson_subject_scope(query, subject_id))
    result = await db.execute(query)
    grades_by_work: dict[int, LessonGrade] = {}
    for grade in dedupe_lesson_grade_rows(result.all()):
        work_number = grade.work_number
        if work_number is None:
            continue
        current = grades_by_work.get(work_number)
        if current is None or _rank_grade(grade) > _rank_grade(current):
            grades_by_work[work_number] = grade
    return grades_by_work


def _build_progress_rows(
    students: list[User],
    states_by_student: dict[UUID, dict[int, ReportLabState]],
    catalog_by_number: dict[int, Lab],
    total_labs: int,
    subgroup: int | None = None,
) -> list[LabProgress]:
    total_students = len(students)
    progress: list[LabProgress] = []
    for work_number in range(1, total_labs + 1):
        completed_count = sum(
            1
            for student in students
            if states_by_student.get(student.id, {}).get(work_number, ReportLabState(None, False)).is_completed
        )
        lab = catalog_by_number.get(work_number)
        progress.append(
            LabProgress(
                lab_name=lab.title if lab else f"Лаб. {work_number}",
                completed_count=completed_count,
                total_students=total_students,
                completion_rate=round(completed_count / total_students * 100, 1) if total_students else 0.0,
                subgroup=subgroup,
            )
        )
    return progress


async def get_group_labs_stats(
    db: AsyncSession,
    group_id: UUID,
    students: list[User],
    settings: AttestationSettings,
    results_map: dict[UUID, Any] | None = None,
    subject_id: UUID | None = None,
) -> dict[UUID, LabStatsMap]:
    resolved, subject_id = await _resolve_subject_id(db, group_id, settings, subject_id)
    policy = await resolve_offering_policy_for_group_subject(
        db,
        group_id=group_id,
        subject_id=subject_id,
        settings=settings,
    )
    required_labs = policy.labs_required_for(settings.attestation_type)
    states_by_student = (
        await _load_completed_states_by_student(
            db, group_id, [student.id for student in students], settings, subject_id
        )
        if resolved
        else {}
    )

    stats: dict[UUID, LabStatsMap] = {}
    for student in students:
        result = results_map.get(student.id) if results_map else None
        completed = (
            result.breakdown.labs_count
            if result is not None
            else sum(1 for state in states_by_student.get(student.id, {}).values() if state.is_completed)
        )
        total = result.breakdown.labs_required if result is not None else required_labs
        stats[student.id] = {"completed": completed, "total": total}
    return stats


async def get_lab_progress(
    db: AsyncSession,
    group_id: UUID,
    students: list[User],
    settings: AttestationSettings,
    has_subgroups: bool = False,
    subject_id: UUID | None = None,
) -> tuple[list[LabProgress], dict[str, list[LabProgress]] | None]:
    resolved, subject_id = await _resolve_subject_id(db, group_id, settings, subject_id)
    policy = await resolve_offering_policy_for_group_subject(
        db,
        group_id=group_id,
        subject_id=subject_id,
        settings=settings,
    )
    total_labs = policy.total_labs
    states_by_student = (
        await _load_completed_states_by_student(
            db, group_id, [student.id for student in students], settings, subject_id
        )
        if resolved
        else {}
    )
    catalog_by_number = await _load_lab_catalog_by_number(db, total_labs, subject_id)
    progress_all = _build_progress_rows(students, states_by_student, catalog_by_number, total_labs)
    if not has_subgroups:
        return progress_all, None

    by_subgroup: dict[str, list[LabProgress]] = {"all": progress_all}
    for subgroup in (1, 2):
        subgroup_students = [student for student in students if student.subgroup == subgroup]
        by_subgroup[str(subgroup)] = _build_progress_rows(
            subgroup_students,
            states_by_student,
            catalog_by_number,
            total_labs,
            subgroup=subgroup,
        )
    return progress_all, by_subgroup
