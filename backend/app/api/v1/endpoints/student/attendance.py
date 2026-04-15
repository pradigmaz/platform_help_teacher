"""Student attendance endpoint."""

from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.audit import ActionType, EntityType, audit_action
from app.models.attendance import Attendance, AttendanceStatus
from app.models.user import User

router = APIRouter()


def build_attendance_stats(records: Sequence[Attendance]) -> dict[str, Any]:
    """Build attendance stats block from attendance records."""
    total = len(records)
    present = sum(1 for record in records if record.status == AttendanceStatus.PRESENT)
    late = sum(1 for record in records if record.status == AttendanceStatus.LATE)
    excused = sum(1 for record in records if record.status == AttendanceStatus.EXCUSED)
    absent = sum(1 for record in records if record.status == AttendanceStatus.ABSENT)
    rate = round((present + late) / total * 100, 1) if total > 0 else 0.0

    return {
        "total_classes": total,
        "present": present,
        "late": late,
        "excused": excused,
        "absent": absent,
        "attendance_rate": rate,
    }


async def list_student_attendance_records(
    db: AsyncSession,
    current_user: User,
) -> list[Attendance]:
    """Fetch attendance records visible for a student."""
    query = select(Attendance).where(Attendance.student_id == current_user.id)
    if current_user.subgroup:
        query = query.where(
            or_(
                Attendance.subgroup.is_(None),
                Attendance.subgroup == current_user.subgroup,
            )
        )

    result = await db.execute(query.order_by(Attendance.date.desc(), Attendance.lesson_number.asc()))
    return list(result.scalars().all())


@router.get("/attendance")
@audit_action(ActionType.VIEW, EntityType.ATTENDANCE)
async def get_my_attendance(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Посещаемость студента со статистикой и деталями занятий."""
    records = await list_student_attendance_records(db, current_user)

    return {
        "stats": build_attendance_stats(records),
        "records": [
            {
                "date": record.date.isoformat(),
                "status": record.status.value,
                "lesson_number": record.lesson_number,
                "lesson_type": record.lesson_type.value if record.lesson_type else None,
            }
            for record in records
        ],
    }
