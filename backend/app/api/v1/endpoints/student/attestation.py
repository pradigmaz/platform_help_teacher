"""Student attestation endpoint."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.attestation_settings import AttestationType
from app.services.attestation_service import AttestationService

router = APIRouter()


@router.get("/attestation/{attestation_type}")
async def get_my_attestation(
    attestation_type: str,
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
        
        return {
            "attestation_type": attestation_type,
            "total_score": result.total_score,
            "lab_score": result.lab_score,
            "attendance_score": result.attendance_score,
            "activity_score": result.activity_score,
            "grade": result.grade,
            "is_passing": result.is_passing,
            "max_points": result.max_points,
            "min_passing_points": result.min_passing_points,
            "breakdown": {
                "labs": {
                    "raw": result.components_breakdown.labs_raw_score,
                    "weighted": result.components_breakdown.labs_weighted_score,
                    "count": result.components_breakdown.labs_count,
                    "required": result.components_breakdown.labs_required,
                },
                "attendance": {
                    "raw": result.components_breakdown.attendance_raw_score,
                    "weighted": result.components_breakdown.attendance_weighted_score,
                    "total_classes": result.components_breakdown.attendance_total_classes,
                    "present": result.components_breakdown.attendance_present,
                    "late": result.components_breakdown.attendance_late,
                },
                "activity": {
                    "raw": result.components_breakdown.activity_raw_score,
                    "weighted": result.components_breakdown.activity_weighted_score,
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
