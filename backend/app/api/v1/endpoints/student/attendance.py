"""Student attendance endpoint."""
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.attendance import Attendance, AttendanceStatus

router = APIRouter()


@router.get("/attendance")
async def get_my_attendance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Посещаемость студента со статистикой."""
    
    query = select(Attendance).where(
        Attendance.student_id == current_user.id
    ).order_by(Attendance.date.desc())
    
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
            }
            for r in records
        ],
    }
