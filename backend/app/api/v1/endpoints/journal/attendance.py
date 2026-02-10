"""
API endpoints для посещаемости журнала.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_teacher, get_db
from app.core import error_messages as em
from app.core.limiter import limiter
from app.models import Attendance, AttendanceStatus, Lesson, User
from app.schemas.lesson_grade import BulkAttendanceUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/attendance")
async def get_journal_attendance(
    group_id: UUID,
    lesson_ids: list[UUID] = Query(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Получить посещаемость для списка занятий."""
    if not lesson_ids:
        return []

    result = await db.execute(
        select(Attendance)
        .where(and_(Attendance.group_id == group_id, Attendance.lesson_id.in_(lesson_ids)))
        .options(selectinload(Attendance.student))
    )
    attendance_list = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "lesson_id": str(a.lesson_id) if a.lesson_id else None,
            "student_id": str(a.student_id),
            "student_name": a.student.full_name if a.student else None,
            "status": a.status.value if hasattr(a.status, "value") else a.status,
            "date": a.date.isoformat(),
            "lesson_number": a.lesson_number,
        }
        for a in attendance_list
    ]


@router.post("/attendance/bulk")
@limiter.limit("30/minute")
async def bulk_update_attendance(
    request: Request,
    data: BulkAttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Массовое обновление посещаемости."""
    lesson_result = await db.execute(
        select(Lesson).where(Lesson.id == data.lesson_id).options(selectinload(Lesson.group))
    )
    lesson = lesson_result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail=em.LESSON_NOT_FOUND)

    # Проверка принадлежности студентов к группе
    group_result = await db.execute(select(User.id).where(User.group_id == lesson.group_id))
    group_student_ids = {row[0] for row in group_result.fetchall()}

    for record in data.records:
        if record.student_id not in group_student_ids:
            raise HTTPException(status_code=400, detail=f"Student {record.student_id} not in group {lesson.group_id}")

    updated = []
    for record in data.records:
        status = AttendanceStatus(record.status)

        # Проверяем по student_id, date, lesson_number (соответствует UniqueConstraint)
        existing_result = await db.execute(
            select(Attendance).where(
                and_(
                    Attendance.student_id == record.student_id,
                    Attendance.date == lesson.date,
                    Attendance.lesson_number == lesson.lesson_number,
                )
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            existing.status = status
            existing.lesson_id = data.lesson_id  # Обновляем lesson_id если был None
            updated.append(existing)
        else:
            new_attendance = Attendance(
                lesson_id=data.lesson_id,
                student_id=record.student_id,
                group_id=lesson.group_id,
                date=lesson.date,
                lesson_number=lesson.lesson_number,
                lesson_type=lesson.lesson_type,
                subgroup=lesson.subgroup,
                status=status,
                created_by=current_user.id,
            )
            db.add(new_attendance)
            updated.append(new_attendance)

    await db.commit()
    logger.info(f"Bulk updated {len(updated)} attendance records for lesson {data.lesson_id}")

    return {"updated": len(updated)}


@router.delete("/attendance")
async def delete_attendance(
    lesson_id: UUID = Query(...),
    student_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Удалить запись посещаемости по lesson_id и student_id."""
    result = await db.execute(
        select(Attendance).where(and_(Attendance.lesson_id == lesson_id, Attendance.student_id == student_id))
    )
    attendance = result.scalar_one_or_none()
    if not attendance:
        return {"deleted": False, "message": "Attendance not found"}

    await db.delete(attendance)
    await db.commit()
    logger.info(f"Deleted attendance for lesson {lesson_id}, student {student_id}")
    return {"deleted": True}
