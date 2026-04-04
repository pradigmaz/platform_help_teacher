"""Lab schedule attachment endpoints."""

import logging
from datetime import date, timedelta
from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import get_current_active_superuser, get_db
from app.core import error_messages as em
from app.models import User
from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.services.lab_attachment_validator import LabAttachmentValidator
from app.services.schedule_constants import today_msk

logger = logging.getLogger(__name__)
router = APIRouter()

SCHEDULE_LOOKAHEAD_DAYS = 14
ATTACHABLE_LESSON_TYPES = (LessonType.LAB, LessonType.PRACTICE)


def _affected_row_count(result: object) -> int:
    rowcount = cast(object, getattr(result, "rowcount", None))
    return rowcount if isinstance(rowcount, int) else 0


class ScheduleSlot(BaseModel):
    lesson_id: str
    date: date
    lesson_number: int
    subgroup: int | None
    current_work_number: int | None
    is_attached: bool  # True if attached to THIS lab


class AttachmentBlockInfo(BaseModel):
    """Информация о блокировке привязки."""

    blocking_lab_number: int | None
    can_attach_from: date | None
    message: str


class GroupSlots(BaseModel):
    group_id: str
    group_name: str
    slots: list[ScheduleSlot]
    attachment_blocked: AttachmentBlockInfo | None = None


class ScheduleSlotsResponse(BaseModel):
    lab_number: int
    groups: list[GroupSlots]
    attachment_blocked: AttachmentBlockInfo | None = None


class AttachRequest(BaseModel):
    lesson_ids: list[str]


class AttachResponse(BaseModel):
    attached_count: int


async def _sync_lab_origin_lesson(db: AsyncSession, lab: Lab) -> None:
    result = await db.execute(
        select(Lesson)
        .where(
            Lesson.work_number == lab.number,
            Lesson.subject_id == lab.subject_id,
            Lesson.lesson_type.in_(ATTACHABLE_LESSON_TYPES),
            Lesson.is_cancelled.is_(False),
        )
        .order_by(Lesson.date, Lesson.lesson_number)
        .limit(1)
    )
    origin_lesson = result.scalar_one_or_none()
    lab.lesson_id = origin_lesson.id if origin_lesson else None


def _same_block_reason(first: AttachmentBlockInfo, second: AttachmentBlockInfo) -> bool:
    return (
        first.blocking_lab_number == second.blocking_lab_number
        and first.can_attach_from == second.can_attach_from
        and first.message == second.message
    )


@router.get("/{lab_id}/schedule-slots", response_model=ScheduleSlotsResponse)
async def get_schedule_slots(
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
):
    """Get available schedule slots for lab attachment."""
    lab = await db.get(Lab, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail=em.LAB_NOT_FOUND)

    today = today_msk()
    end_date = today + timedelta(days=SCHEDULE_LOOKAHEAD_DAYS)

    # Build filter
    filters = [
        Lesson.lesson_type.in_(ATTACHABLE_LESSON_TYPES),
        Lesson.date >= today,
        Lesson.date <= end_date,
        Lesson.is_cancelled.is_(False),
    ]
    if lab.subject_id:
        filters.append(Lesson.subject_id == lab.subject_id)

    # Load lessons with groups
    query = (
        select(Lesson)
        .options(joinedload(Lesson.group))
        .where(and_(*filters))
        .order_by(Lesson.date, Lesson.lesson_number)
    )
    result = await db.execute(query)
    lessons = result.scalars().unique().all()

    # Group by group_id
    groups_map: dict[UUID, GroupSlots] = {}
    for lesson in lessons:
        if lesson.group_id not in groups_map:
            groups_map[lesson.group_id] = GroupSlots(
                group_id=str(lesson.group_id), group_name=lesson.group.name if lesson.group else "???", slots=[]
            )

        groups_map[lesson.group_id].slots.append(
            ScheduleSlot(
                lesson_id=str(lesson.id),
                date=lesson.date,
                lesson_number=lesson.lesson_number,
                subgroup=lesson.subgroup,
                current_work_number=lesson.work_number,
                is_attached=lesson.work_number == lab.number,
            )
        )

    # Проверяем блокировку привязки для каждой группы отдельно.
    attachment_blocked = None
    if lessons and lab.number > 1:
        validator = LabAttachmentValidator(db)
        group_blocks: list[AttachmentBlockInfo] = []
        for group in groups_map.values():
            if not group.slots:
                continue
            first_slot = group.slots[0]
            validation = await validator.validate_attachment(
                lab_to_attach=lab,
                target_lesson_date=first_slot.date,
                group_id=UUID(group.group_id),
                subject_id=lab.subject_id,
            )
            if not validation.is_valid:
                group.attachment_blocked = AttachmentBlockInfo(
                    blocking_lab_number=validation.blocking_lab_number,
                    can_attach_from=validation.can_attach_from,
                    message=validation.message,
                )
                group_blocks.append(group.attachment_blocked)

        if group_blocks and len(group_blocks) == len(groups_map):
            first_block = group_blocks[0]
            if all(_same_block_reason(first_block, block) for block in group_blocks[1:]):
                attachment_blocked = first_block

    return ScheduleSlotsResponse(
        lab_number=lab.number, groups=list(groups_map.values()), attachment_blocked=attachment_blocked
    )


@router.post("/{lab_id}/attach", response_model=AttachResponse)
async def attach_to_lessons(
    lab_id: UUID,
    data: AttachRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    """Attach lab to schedule lessons."""
    lab = await db.get(Lab, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail=em.LAB_NOT_FOUND)

    if not data.lesson_ids:
        return AttachResponse(attached_count=0)

    lesson_uuids = [UUID(lid) for lid in data.lesson_ids]

    # Получаем первое занятие для валидации
    lessons_result = await db.execute(select(Lesson).where(Lesson.id.in_(lesson_uuids)))
    lessons = lessons_result.scalars().all()
    if len(lessons) != len(lesson_uuids):
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)

    validator = LabAttachmentValidator(db)
    for lesson in lessons:
        validation = await validator.validate_attachment(
            lab_to_attach=lab,
            target_lesson_date=lesson.date,
            group_id=lesson.group_id,
            subject_id=lab.subject_id,
        )

        if not validation.is_valid:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "previous_lab_active",
                    "blocking_lab_number": validation.blocking_lab_number,
                    "can_attach_from": validation.can_attach_from.isoformat() if validation.can_attach_from else None,
                    "message": validation.message,
                },
            )

    # Update work_number for selected lessons
    stmt = (
        update(Lesson)
        .where(Lesson.id.in_(lesson_uuids))
        .where(Lesson.lesson_type.in_(ATTACHABLE_LESSON_TYPES))
        .values(work_number=lab.number)
    )
    result = await db.execute(stmt)
    attached_count = _affected_row_count(result)
    await _sync_lab_origin_lesson(db, lab)
    await db.commit()

    logger.info(f"Admin {admin.id} attached lab {lab.number} to {attached_count} lessons")

    return AttachResponse(attached_count=attached_count)


@router.post("/{lab_id}/detach", response_model=AttachResponse)
async def detach_from_lessons(
    lab_id: UUID,
    data: AttachRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    """Detach lab from schedule lessons."""
    lab = await db.get(Lab, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail=em.LAB_NOT_FOUND)

    if not data.lesson_ids:
        return AttachResponse(attached_count=0)

    lesson_uuids = [UUID(lid) for lid in data.lesson_ids]

    # Clear work_number only for lessons attached to THIS lab
    stmt = (
        update(Lesson)
        .where(Lesson.id.in_(lesson_uuids))
        .where(Lesson.work_number == lab.number)
        .values(work_number=None)
    )
    result = await db.execute(stmt)
    detached_count = _affected_row_count(result)
    await _sync_lab_origin_lesson(db, lab)
    await db.commit()

    logger.info(f"Admin {admin.id} detached lab {lab.number} from {detached_count} lessons")

    return AttachResponse(attached_count=detached_count)
