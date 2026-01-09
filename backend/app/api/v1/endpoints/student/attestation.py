"""Student attestation endpoint."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.attestation_settings import AttestationType
from app.services.attestation_service import AttestationService
from app.audit import audit_action, ActionType, EntityType

router = APIRouter()


@router.get("/attestation/{attestation_type}")
@audit_action(ActionType.VIEW, EntityType.ATTESTATION)
async def get_my_attestation(
    attestation_type: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Баллы аттестации студента."""
    
    if attestation_type not in ("first", "second"):
        raise HTTPException(status_code=400, detail="Invalid attestation type")
    
    if not current_user.group_id:
        return {
            "attestation_type": attestation_type,
            "error": "Студент не привязан к группе",
            "total_score": 0,
            "grade": "-",
            "is_passing": False,
        }
    
    try:
        att_type = AttestationType.FIRST if attestation_type == "first" else AttestationType.SECOND
        
        service = AttestationService(db)
        result = await service.calculate_student_score(
            student_id=current_user.id,
            group_id=current_user.group_id,
            attestation_type=att_type,
            activity_points=0,
        )
        
        b = result.breakdown
        return {
            "attestation_type": attestation_type,
            "total_score": result.total_score,
            "grade": result.grade,
            "is_passing": result.is_passing,
            "max_points": result.max_points,
            "min_passing_points": result.min_passing_points,
            "breakdown": {
                "labs": {
                    "score": b.labs_score,
                    "max": b.labs_max,
                    "count": b.labs_count,
                },
                "attendance": {
                    "score": b.attendance_score,
                    "max": b.attendance_max,
                    "ratio": b.attendance_ratio,
                    "total_classes": b.total_classes,
                    "present": b.present_count,
                    "late": b.late_count,
                },
                "activity": {
                    "score": b.activity_score,
                    "max": b.activity_max,
                    "bonus_blocked": b.bonus_blocked,
                },
            },
        }
    except Exception as e:
        return {
            "attestation_type": attestation_type,
            "error": str(e) or "Настройки аттестации не найдены",
            "total_score": 0,
            "grade": "-",
            "is_passing": False,
        }
