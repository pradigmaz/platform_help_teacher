"""Student attendance endpoint."""

from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.audit import ActionType, EntityType, audit_action
from app.models.attendance import Attendance, AttendanceStatus
from app.models.user import User

router = APIRouter()


@router.get("/attendance")
@audit_action(ActionType.VIEW, EntityType.ATTENDANCE)
async def get_my_attendance(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Посещаемость студента со статистикой и деталями занятий."""

    # Фильтр по подгруппе: показываем записи без подгруппы (лекции) + записи подгруппы студента
    query = select(Attendance).where(Attendance.student_id == current_user.id)

    # Если у студента есть подгруппа — фильтруем
    if current_user.subgroup:
        query = query.where(
            or_(
                Attendance.subgroup.is_(None),  # Лекции (без подгруппы)
                Attendance.subgroup == current_user.subgroup,  # Его подгруппа
            )
        )

    query = query.order_by(Attendance.date.desc(), Attendance.lesson_number.asc())

    result = await db.execute(query)
    records = result.scalars().all()

    # Статистика
    total = len(records)
    present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
    late = sum(1 for r in records if r.status == AttendanceStatus.LATE)
    excused = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED)
    absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)

    rate = round((present + late) / total * 100, 1) if total > 0 else 0.0

    return {
        "stats": {
            "total_classes": total,
            "present": present,
            "late": late,
            "excused": excused,
            "absent": absent,
            "attendance_rate": rate,
        },
        "records": [
            {
                "date": r.date.isoformat(),
                "status": r.status.value,
                "lesson_number": r.lesson_number,
                "lesson_type": r.lesson_type.value if r.lesson_type else None,
            }
            for r in records
        ],
    }
