"""Lab schedule attachment endpoints."""
import logging
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import get_db, get_current_active_superuser
from app.models import User
from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.group import Group
from app.models.schedule import LessonType
from app.services.schedule_constants import today_msk
from app.services.lab_attachment_validator import LabAttachmentValidator

logger = logging.getLogger(__name__)
router = APIRouter()

SCHEDULE_LOOKAHEAD_DAYS = 14


class ScheduleSlot(BaseModel):
    lesson_id: str
    date: date
    lesson_number: int
    subgroup: int | None
    current_work_number: int | None
    is_attached: bool  # True if attached to THIS lab


class GroupSlots(BaseModel):
    group_id: str
    group_name: str
    slots: List[ScheduleSlot]


class AttachmentBlockInfo(BaseModel):
    """Информация о блокировке привязки."""
    blocking_lab_number: int
    can_attach_from: Optional[date]
    message: str


class ScheduleSlotsResponse(BaseModel):
    lab_number: int
    groups: List[GroupSlots]
    attachment_blocked: Optional[AttachmentBlockInfo] = None


class AttachRequest(BaseModel):
    lesson_ids: List[str]


class AttachResponse(BaseModel):
    attached_count: int


@router.get("/{lab_id}/schedule-slots", response_model=ScheduleSlotsResponse)
async def get_schedule_slots(
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
):
    """Get available schedule slots for lab attachment."""
    lab = await db.get(Lab, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    
    today = today_msk()
    end_date = today + timedelta(days=SCHEDULE_LOOKAHEAD_DAYS)
    
    # Build filter
    filters = [
        Lesson.lesson_type == LessonType.LAB,
        Lesson.date >= today,
        Lesson.date <= end_date,
        Lesson.is_cancelled == False,
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
                group_id=str(lesson.group_id),
                group_name=lesson.group.name if lesson.group else "???",
                slots=[]
            )
        
        groups_map[lesson.group_id].slots.append(ScheduleSlot(
            lesson_id=str(lesson.id),
            date=lesson.date,
            lesson_number=lesson.lesson_number,
            subgroup=lesson.subgroup,
            current_work_number=lesson.work_number,
            is_attached=lesson.work_number == lab.number,
        ))
    
    # Проверяем блокировку привязки для каждой группы
    attachment_blocked = None
    if lessons and lab.number > 1:
        validator = LabAttachmentValidator(db)
        # Проверяем для первой группы (блокировка одинакова для всех)
        first_lesson = lessons[0]
        validation = await validator.validate_attachment(
            lab_to_attach=lab,
            target_lesson_date=first_lesson.date,
            group_id=first_lesson.group_id,
            subject_id=lab.subject_id
        )
        if not validation.is_valid:
            attachment_blocked = AttachmentBlockInfo(
                blocking_lab_number=validation.blocking_lab_number,
                can_attach_from=validation.can_attach_from,
                message=validation.message
            )
    
    return ScheduleSlotsResponse(
        lab_number=lab.number,
        groups=list(groups_map.values()),
        attachment_blocked=attachment_blocked
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
        raise HTTPException(status_code=404, detail="Lab not found")
    
    if not data.lesson_ids:
        return AttachResponse(attached_count=0)
    
    lesson_uuids = [UUID(lid) for lid in data.lesson_ids]
    
    # Получаем первое занятие для валидации
    first_lesson = await db.get(Lesson, lesson_uuids[0])
    if not first_lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Валидация: проверяем не активна ли предыдущая лаба
    validator = LabAttachmentValidator(db)
    validation = await validator.validate_attachment(
        lab_to_attach=lab,
        target_lesson_date=first_lesson.date,
        group_id=first_lesson.group_id,
        subject_id=lab.subject_id
    )
    
    if not validation.is_valid:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "previous_lab_active",
                "blocking_lab_number": validation.blocking_lab_number,
                "can_attach_from": validation.can_attach_from.isoformat() if validation.can_attach_from else None,
                "message": validation.message
            }
        )
    
    # Update work_number for selected lessons
    stmt = (
        update(Lesson)
        .where(Lesson.id.in_(lesson_uuids))
        .where(Lesson.lesson_type == LessonType.LAB)
        .values(work_number=lab.number)
    )
    result = await db.execute(stmt)
    await db.commit()
    
    logger.info(f"Admin {admin.id} attached lab {lab.number} to {result.rowcount} lessons")
    
    return AttachResponse(attached_count=result.rowcount)


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
        raise HTTPException(status_code=404, detail="Lab not found")
    
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
    await db.commit()
    
    logger.info(f"Admin {admin.id} detached lab {lab.number} from {result.rowcount} lessons")
    
    return AttachResponse(attached_count=result.rowcount)
