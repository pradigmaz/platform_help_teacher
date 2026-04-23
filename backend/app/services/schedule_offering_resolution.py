"""Resolve and validate subject/offering scope for schedule and lesson writes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_group_subject_offering import (
    ensure_group_subject_offering_for_date,
    get_group_subject_offering_for_date,
)
from app.models.group_subject_offering import GroupSubjectOffering
from app.services.semester_utils import get_semester


@dataclass(frozen=True)
class ResolvedOfferingScope:
    subject_id: UUID | None
    offering_id: UUID | None


def combine_resolved_scopes(
    preferred: ResolvedOfferingScope,
    fallback: ResolvedOfferingScope,
) -> ResolvedOfferingScope:
    """Merge two resolved scopes and fail on contradictory subject/offering identities."""
    if preferred.subject_id and fallback.subject_id and preferred.subject_id != fallback.subject_id:
        raise ValueError("Предмет занятия не совпадает с элементом расписания")
    if preferred.offering_id and fallback.offering_id and preferred.offering_id != fallback.offering_id:
        raise ValueError("Семестровое назначение занятия не совпадает с элементом расписания")
    return ResolvedOfferingScope(
        subject_id=preferred.subject_id or fallback.subject_id,
        offering_id=preferred.offering_id or fallback.offering_id,
    )


async def resolve_schedule_offering_scope(
    db: AsyncSession,
    *,
    group_id: UUID,
    reference_date: date,
    subject_id: UUID | None = None,
    offering_id: UUID | None = None,
    ensure: bool = False,
    require_existing: bool = False,
) -> ResolvedOfferingScope:
    """Resolve a consistent `(subject_id, offering_id)` pair for schedule/lesson writes."""
    if offering_id is not None:
        offering = await db.get(GroupSubjectOffering, offering_id)
        if offering is None:
            raise ValueError("Семестровое назначение предмета не найдено")
        if offering.group_id != group_id:
            raise ValueError("Семестровое назначение не принадлежит выбранной группе")
        if offering.semester != get_semester(reference_date):
            raise ValueError("Семестровое назначение не соответствует дате занятия")
        if subject_id is not None and offering.subject_id != subject_id:
            raise ValueError("Предмет не совпадает с выбранным семестровым назначением")
        return ResolvedOfferingScope(subject_id=offering.subject_id, offering_id=offering.id)

    if subject_id is None:
        return ResolvedOfferingScope(subject_id=None, offering_id=None)

    offering = await _resolve_offering_by_subject(
        db,
        group_id=group_id,
        subject_id=subject_id,
        reference_date=reference_date,
        ensure=ensure,
    )
    if offering is None and require_existing:
        raise ValueError("Для группы и предмета не найдено семестровое назначение")
    return ResolvedOfferingScope(subject_id=subject_id, offering_id=offering.id if offering else None)


async def resolve_schedule_scope_from_item(
    db: AsyncSession,
    *,
    group_id: UUID,
    reference_date: date,
    schedule_item_id: UUID | None,
) -> ResolvedOfferingScope:
    """Derive subject/offering scope from a linked schedule item if one exists."""
    if schedule_item_id is None:
        return ResolvedOfferingScope(subject_id=None, offering_id=None)

    from app.models.schedule import ScheduleItem

    item = await db.get(ScheduleItem, schedule_item_id)
    if item is None:
        raise ValueError("Элемент расписания не найден")
    if item.group_id != group_id:
        raise ValueError("Элемент расписания не принадлежит выбранной группе")
    return await resolve_schedule_offering_scope(
        db,
        group_id=group_id,
        reference_date=reference_date,
        subject_id=cast(UUID | None, item.subject_id),
        offering_id=cast(UUID | None, item.offering_id),
        require_existing=False,
    )


async def _resolve_offering_by_subject(
    db: AsyncSession,
    *,
    group_id: UUID,
    subject_id: UUID,
    reference_date: date,
    ensure: bool,
) -> GroupSubjectOffering | None:
    if ensure:
        return await ensure_group_subject_offering_for_date(
            db,
            group_id=group_id,
            subject_id=subject_id,
            lesson_date=reference_date,
        )
    return await get_group_subject_offering_for_date(
        db,
        group_id=group_id,
        subject_id=subject_id,
        lesson_date=reference_date,
    )


def validate_schedule_item_date_range(
    *,
    start_date: date,
    end_date: date | None,
    subject_id: UUID | None,
    offering_id: UUID | None,
) -> None:
    """Reject subject-bound schedule items that span multiple semesters."""
    if end_date is None:
        return
    if end_date < start_date:
        raise ValueError("Дата окончания не может быть раньше даты начала")
    if subject_id is None and offering_id is None:
        return
    if get_semester(start_date) == get_semester(end_date):
        return
    raise ValueError("Предметное расписание не может пересекать границу семестра")
