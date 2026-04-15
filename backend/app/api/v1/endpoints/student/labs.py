"""Student labs endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.endpoints.student.lab_queries import get_student_lab_detail_response, list_student_labs
from app.audit import ActionType, EntityType, audit_action
from app.audit.deps import audit_user
from app.core import error_messages as em
from app.core.limiter import limiter
from app.models.user import User
from app.services.lab_visibility import LabVisibilityService
from app.services.student_lab_service import student_lab_service

router = APIRouter()


@router.get("/labs")
@audit_action(ActionType.VIEW, EntityType.LAB)
async def get_my_labs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Лабораторные работы студента со статусами сдачи."""
    return await list_student_labs(db, current_user)


@router.get("/labs/{lab_id}")
@audit_action(ActionType.VIEW, EntityType.LAB_DETAIL, "lab_id")
async def get_lab_detail(
    lab_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Детали лабораторной работы с вариантом студента."""
    return await get_student_lab_detail_response(db, current_user, lab_id)


@router.post("/labs/{lab_id}/ready")
@limiter.limit("10/hour")
@audit_action(ActionType.SUBMIT, EntityType.SUBMISSION, "lab_id")
async def mark_lab_ready(
    lab_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(audit_user),
) -> dict[str, Any]:
    """Отметить лабу как готовую к сдаче. Rate limit: 10/hour."""
    lab = await student_lab_service.get_lab_by_id(db, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail=em.LAB_NOT_FOUND)

    if current_user.group_id:
        visibility_service = LabVisibilityService(db)
        visibility_info = await visibility_service.get_visibility_info(
            lab_number=lab.number,
            group_id=current_user.group_id,
            subgroup=current_user.subgroup,
            deadline_5_lessons=lab.deadline_5_lessons,
            deadline_4_lessons=lab.deadline_4_lessons,
            subject_id=lab.subject_id,
            lab_id=lab.id,
            student_id=current_user.id,
        )
        if not visibility_info.is_visible:
            raise HTTPException(status_code=403, detail=em.LAB_NOT_AVAILABLE_BY_SCHEDULE)

        current_lesson = await visibility_service.get_current_lab_session(
            group_id=current_user.group_id,
            subgroup=current_user.subgroup,
            subject_id=lab.subject_id,
        )
        if not current_lesson:
            raise HTTPException(status_code=403, detail="Сдача доступна только во время пары")
    else:
        current_lesson = None

    is_available = await student_lab_service.check_lab_availability(db, current_user.id, lab)
    if not is_available:
        raise HTTPException(status_code=403, detail=em.LAB_NOT_AVAILABLE_YET)

    student_position = await student_lab_service.get_student_position(db, current_user)
    variant_number = None
    if lab.variants and student_position:
        variant_number = ((student_position - 1) % len(lab.variants)) + 1

    try:
        sub = await student_lab_service.mark_ready(
            db,
            current_user.id,
            lab_id,
            variant_number,
            lesson=current_lesson,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "ready",
        "submission_id": str(sub.id),
        "variant_number": variant_number,
        "message": "You are now in the queue.",
    }


@router.post("/labs/{lab_id}/cancel-ready")
@audit_action(ActionType.CANCEL, EntityType.SUBMISSION, "lab_id")
async def cancel_lab_ready(
    lab_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(audit_user),
) -> dict[str, Any]:
    """Отменить готовность к сдаче."""
    try:
        await student_lab_service.cancel_ready(db, current_user.id, lab_id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    return {"status": "cancelled", "message": "Removed from queue"}
