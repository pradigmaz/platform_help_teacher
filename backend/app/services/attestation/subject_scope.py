"""Subject-aware helpers for attestation calculations."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_group_subject_offering import get_current_semester_key
from app.models.attestation_settings import AttestationSettings
from app.models.group_subject_offering import GroupSubjectOffering
from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.models.student_transfer import StudentTransfer
from app.models.subject import Subject

LAB_RELEVANT_LESSON_TYPES = (LessonType.LAB, LessonType.PRACTICE)
TRANSFER_COUNT_KEYS = ("total_lessons", "present", "late", "excused", "absent")


@dataclass(frozen=True)
class AttestationSubjectScope:
    """Resolved subject context for a single attestation calculation."""

    subject_id: UUID | None
    period_subject_ids: tuple[UUID, ...]
    allow_legacy_unscoped: bool

    @property
    def can_use_legacy_activity_points(self) -> bool:
        return self.allow_legacy_unscoped


async def list_group_subject_ids_in_period(
    db: AsyncSession,
    group_id: UUID,
    settings: AttestationSettings,
) -> tuple[UUID, ...]:
    """List distinct subjects for the active semester, preferring offerings over lessons."""
    semester_key = await get_current_semester_key(db)
    offerings_result = await db.execute(
        select(GroupSubjectOffering.subject_id)
        .where(
            GroupSubjectOffering.group_id == group_id,
            GroupSubjectOffering.semester == semester_key,
        )
        .distinct()
    )
    offering_subject_ids = tuple(subject_id for subject_id in offerings_result.scalars().all() if subject_id is not None)
    if offering_subject_ids:
        return offering_subject_ids

    period_start, period_end = settings.get_effective_period()
    lessons_result = await db.execute(
        select(Lesson.subject_id)
        .where(Lesson.group_id == group_id)
        .where(Lesson.subject_id.isnot(None))
        .where(Lesson.is_cancelled.is_(False))
        .where(Lesson.date >= period_start)
        .where(Lesson.date <= period_end)
        .distinct()
    )
    return tuple(subject_id for subject_id in lessons_result.scalars().all() if subject_id is not None)


async def resolve_attestation_subject_scope(
    db: AsyncSession,
    group_id: UUID,
    settings: AttestationSettings,
    requested_subject_id: UUID | None = None,
) -> AttestationSubjectScope:
    """Resolve a safe subject scope for attestation calculations."""
    period_subject_ids = await list_group_subject_ids_in_period(db, group_id, settings)

    if requested_subject_id is not None:
        if period_subject_ids and requested_subject_id not in period_subject_ids:
            raise ValueError("Предмет не найден в выбранном периоде аттестации")
        return AttestationSubjectScope(
            subject_id=requested_subject_id,
            period_subject_ids=period_subject_ids,
            allow_legacy_unscoped=True,
        )

    if len(period_subject_ids) > 1:
        raise ValueError("Для расчёта аттестации по нескольким предметам нужно выбрать предмет")

    resolved_subject_id = period_subject_ids[0] if period_subject_ids else None
    return AttestationSubjectScope(
        subject_id=resolved_subject_id,
        period_subject_ids=period_subject_ids,
        allow_legacy_unscoped=True,
    )


async def list_group_subject_options_in_period(
    db: AsyncSession,
    group_id: UUID,
    settings: AttestationSettings,
) -> list[Subject]:
    """List subject records available for attestation in the period."""
    semester_key = await get_current_semester_key(db)
    offerings_result = await db.execute(
        select(Subject)
        .join(GroupSubjectOffering, GroupSubjectOffering.subject_id == Subject.id)
        .where(
            GroupSubjectOffering.group_id == group_id,
            GroupSubjectOffering.semester == semester_key,
        )
        .distinct()
        .order_by(Subject.name.asc())
    )
    offering_subjects = list(offerings_result.scalars().all())
    if offering_subjects:
        return offering_subjects

    period_start, period_end = settings.get_effective_period()
    lessons_result = await db.execute(
        select(Subject)
        .join(Lesson, Lesson.subject_id == Subject.id)
        .where(Lesson.group_id == group_id)
        .where(Lesson.subject_id.isnot(None))
        .where(Lesson.is_cancelled.is_(False))
        .where(Lesson.date >= period_start)
        .where(Lesson.date <= period_end)
        .distinct()
        .order_by(Subject.name.asc())
    )
    return list(lessons_result.scalars().all())


def apply_lesson_subject_scope(query, subject_id: UUID | None):
    """Apply optional subject filter to a Lesson-joined query."""
    if subject_id is None:
        return query
    return query.where(Lesson.subject_id == subject_id)


def apply_lab_lesson_type_scope(query):
    """Keep only lab-bearing lessons in attestation lab queries."""
    return query.where(Lesson.lesson_type.in_(LAB_RELEVANT_LESSON_TYPES))


def filter_external_lab_grade_payloads(
    rows: list[dict[str, Any]] | None,
    subject_id: UUID | None,
) -> list[dict[str, Any]]:
    """Keep only lab-grade payloads relevant to the resolved subject."""
    if not rows:
        return []
    if subject_id is None:
        return list(rows)

    subject_key = str(subject_id)
    return [row for row in rows if str(row.get("subject_id") or "") == subject_key]


def merge_transfer_attendance(
    transfers: list[StudentTransfer],
    scope: AttestationSubjectScope,
) -> dict[str, int] | None:
    """Merge transfer attendance snapshots without mixing unrelated subjects."""
    merged = {key: 0 for key in TRANSFER_COUNT_KEYS}

    for transfer in transfers:
        snapshot = _get_transfer_subject_snapshot(transfer, scope)
        if not snapshot:
            continue
        for key in TRANSFER_COUNT_KEYS:
            merged[key] += int(snapshot.get(key, 0) or 0)

    return merged if merged["total_lessons"] > 0 else None


def merge_transfer_lab_grades(
    transfers: list[StudentTransfer],
    scope: AttestationSubjectScope,
) -> list[dict[str, Any]]:
    """Merge transfer lab-grade payloads with subject filtering."""
    all_grades: list[dict[str, Any]] = []

    for transfer in transfers:
        for grade_data in transfer.lab_grades_data or []:
            if scope.subject_id is not None and str(grade_data.get("subject_id") or "") != str(scope.subject_id):
                continue
            all_grades.append(grade_data)

    return all_grades


def sum_transfer_activity_points(
    transfers: list[StudentTransfer],
    scope: AttestationSubjectScope,
) -> float:
    """Sum transfer activity points without silently cross-counting subjects."""
    total = 0.0

    for transfer in transfers:
        subject_snapshot = _get_transfer_subject_snapshot(transfer, scope)
        if subject_snapshot is not None and "activity_points" in subject_snapshot:
            total += float(subject_snapshot.get("activity_points") or 0.0)
            continue
        if scope.allow_legacy_unscoped:
            total += float(transfer.activity_points or 0.0)

    return total


def _get_transfer_subject_snapshot(
    transfer: StudentTransfer,
    scope: AttestationSubjectScope,
) -> dict[str, Any] | None:
    attendance_data = transfer.attendance_data or {}

    if scope.subject_id is not None:
        subject_snapshots = attendance_data.get("subjects") or {}
        subject_snapshot = subject_snapshots.get(str(scope.subject_id))
        if isinstance(subject_snapshot, dict):
            return subject_snapshot
        if not scope.allow_legacy_unscoped:
            return None

    return {key: int(attendance_data.get(key, 0) or 0) for key in TRANSFER_COUNT_KEYS}
