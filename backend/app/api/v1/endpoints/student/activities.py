"""Student activities endpoint — история начислений/штрафов."""

from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.activity import Activity
from app.models.user import User

router = APIRouter()


@router.get("/activities")
async def get_my_activities(
    request: Request,
    attestation_type: str = "first",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    История активностей студента (бонусы/штрафы).

    Показывает за что начислены или сняты баллы.
    """
    if attestation_type not in ("first", "second"):
        attestation_type = "first"

    result = await db.execute(
        select(Activity)
        .where(
            Activity.student_id == current_user.id,
            Activity.attestation_type == attestation_type,
            Activity.is_active,
        )
        .order_by(Activity.created_at.desc())
    )
    activities = result.scalars().all()

    # Статистика
    total_bonus = sum(a.points for a in activities if a.points > 0)
    total_penalty = sum(a.points for a in activities if a.points < 0)

    return {
        "attestation_type": attestation_type,
        "stats": {
            "total_bonus": round(total_bonus, 2),
            "total_penalty": round(total_penalty, 2),
            "net_total": round(total_bonus + total_penalty, 2),
            "count": len(activities),
        },
        "activities": [
            {
                "id": str(a.id),
                "points": a.points,
                "description": a.description,
                "created_at": a.created_at.isoformat(),
            }
            for a in activities
        ],
    }
