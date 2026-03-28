"""Shared input loaders for deadline evaluation paths."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance, AttendanceStatus
from app.models.lab_deadline_extension import LabDeadlineExtension
from app.models.lesson import Lesson


async def load_active_extension_bonus_map(
    db: AsyncSession,
    *,
    lab_ids: set[UUID],
    group_id: UUID | None,
    now: datetime | None = None,
) -> dict[UUID, int]:
    """Load active extension bonuses for a group in one query."""
    if not lab_ids or group_id is None:
        return {}

    effective_now = now or datetime.now(UTC)
    result = await db.execute(
        select(LabDeadlineExtension.lab_id, LabDeadlineExtension.bonus_lessons).where(
            and_(
                LabDeadlineExtension.lab_id.in_(lab_ids),
                LabDeadlineExtension.group_id == group_id,
                LabDeadlineExtension.is_active,
                (LabDeadlineExtension.expires_at.is_(None)) | (LabDeadlineExtension.expires_at > effective_now),
            )
        )
    )
    return {lab_id: bonus for lab_id, bonus in result.fetchall()}


async def load_active_extension_bonus(
    db: AsyncSession,
    *,
    lab_id: UUID,
    group_id: UUID | None,
    now: datetime | None = None,
) -> int:
    """Load active extension bonus for one lab/group pair."""
    return (await load_active_extension_bonus_map(db, lab_ids={lab_id}, group_id=group_id, now=now)).get(lab_id, 0)


async def load_excused_origin_numbers(
    db: AsyncSession,
    *,
    student_id: UUID | None,
    origin_lessons_by_number: dict[int, Lesson],
) -> set[int]:
    """Return lab numbers where student was EXCUSED on the resolved origin lesson only."""
    if student_id is None or not origin_lessons_by_number:
        return set()

    origin_lesson_ids = {lesson.id for lesson in origin_lessons_by_number.values()}
    result = await db.execute(
        select(Attendance.lesson_id).where(
            and_(
                Attendance.lesson_id.in_(origin_lesson_ids),
                Attendance.student_id == student_id,
                Attendance.status == AttendanceStatus.EXCUSED,
            )
        )
    )
    excused_lesson_ids = {lesson_id for (lesson_id,) in result.all()}
    return {
        lab_number
        for lab_number, lesson in origin_lessons_by_number.items()
        if lesson.id in excused_lesson_ids
    }
