"""Student labs endpoints."""
from typing import Any, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.models.lab import Lab
from app.models.submission import Submission, SubmissionStatus
from app.audit import audit_action, audit_user, ActionType, EntityType

router = APIRouter()


@router.get("/labs")
async def get_my_labs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Лабораторные работы студента со статусами сдачи."""
    
    labs_result = await db.execute(
        select(Lab).order_by(Lab.number.asc(), Lab.created_at.desc())
    )
    labs = labs_result.scalars().all()
    
    subs_result = await db.execute(
        select(Submission).where(Submission.user_id == current_user.id)
    )
    submissions = {s.lab_id: s for s in subs_result.scalars().all()}
    
    student_position = await _get_student_position(db, current_user)
    
    result = []
    prev_accepted = True
    
    for lab in labs:
        sub = submissions.get(lab.id)
        is_available = prev_accepted or not lab.is_sequential
        
        variant_number = None
        if lab.variants and student_position:
            variants_count = len(lab.variants)
            variant_number = ((student_position - 1) % variants_count) + 1
        
        result.append({
            "id": str(lab.id),
            "number": lab.number,
            "title": lab.title,
            "topic": lab.topic,
            "description": lab.description,
            "deadline": lab.deadline.isoformat() if lab.deadline else None,
            "max_grade": lab.max_grade,
            "is_available": is_available,
            "variant_number": variant_number,
            "submission": _format_submission(sub) if sub else None,
        })
        
        if sub and sub.status.value == "ACCEPTED":
            prev_accepted = True
        elif lab.is_sequential:
            prev_accepted = False
    
    return result


@router.get("/labs/{lab_id}")
async def get_lab_detail(
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Детали лабораторной работы с вариантом студента."""
    lab = await db.get(Lab, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    
    is_available = await _check_lab_availability(db, current_user.id, lab)
    student_position = await _get_student_position(db, current_user)
    
    variant_number = None
    variant_data = None
    if lab.variants and student_position:
        variants_count = len(lab.variants)
        variant_number = ((student_position - 1) % variants_count) + 1
        for v in lab.variants:
            if v.get("number") == variant_number:
                variant_data = v
                break
    
    sub_result = await db.execute(
        select(Submission).where(
            Submission.user_id == current_user.id,
            Submission.lab_id == lab_id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    
    return {
        "id": str(lab.id),
        "number": lab.number,
        "title": lab.title,
        "topic": lab.topic,
        "goal": lab.goal,
        "formatting_guide": lab.formatting_guide,
        "theory_content": lab.theory_content,
        "practice_content": lab.practice_content,
        "questions": lab.questions,
        "deadline": lab.deadline.isoformat() if lab.deadline else None,
        "max_grade": lab.max_grade,
        "is_available": is_available,
        "variant_number": variant_number,
        "variant_data": variant_data,
        "submission": _format_submission(sub) if sub else None,
    }


@router.post("/labs/{lab_id}/ready")
@audit_action(ActionType.SUBMIT, EntityType.SUBMISSION, "lab_id")
async def mark_lab_ready(
    lab_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(audit_user),
) -> dict[str, Any]:
    """Отметить лабу как готовую к сдаче."""
    lab = await db.get(Lab, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    
    is_available = await _check_lab_availability(db, current_user.id, lab)
    if not is_available:
        raise HTTPException(status_code=403, detail="Lab is not available yet")
    
    sub_result = await db.execute(
        select(Submission).where(
            Submission.user_id == current_user.id,
            Submission.lab_id == lab_id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    
    if sub:
        if sub.status.value == "READY":
            raise HTTPException(status_code=400, detail="Already in queue")
        if sub.status.value == "ACCEPTED":
            raise HTTPException(status_code=400, detail="Lab already accepted")
    
    student_position = await _get_student_position(db, current_user)
    variant_number = None
    if lab.variants and student_position:
        variants_count = len(lab.variants)
        variant_number = ((student_position - 1) % variants_count) + 1
    
    if sub:
        sub.status = SubmissionStatus.READY
        sub.ready_at = datetime.utcnow()
        sub.variant_number = variant_number
    else:
        sub = Submission(
            user_id=current_user.id,
            lab_id=lab_id,
            status=SubmissionStatus.READY,
            is_manual=True,
            variant_number=variant_number,
            ready_at=datetime.utcnow(),
        )
        db.add(sub)
    
    await db.commit()
    await db.refresh(sub)
    
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
    sub_result = await db.execute(
        select(Submission).where(
            Submission.user_id == current_user.id,
            Submission.lab_id == lab_id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if sub.status.value != "READY":
        raise HTTPException(status_code=400, detail="Not in queue")
    
    sub.status = SubmissionStatus.NEW
    sub.ready_at = None
    await db.commit()
    
    return {"status": "cancelled", "message": "Removed from queue"}


# === Helpers ===

def _format_submission(sub: Submission) -> dict:
    return {
        "id": str(sub.id),
        "status": sub.status.value,
        "grade": sub.grade,
        "feedback": sub.feedback,
        "ready_at": sub.ready_at.isoformat() if sub.ready_at else None,
        "accepted_at": sub.accepted_at.isoformat() if sub.accepted_at else None,
    }


async def _get_student_position(db: AsyncSession, user: User) -> Optional[int]:
    """Получить позицию студента в списке группы."""
    if not user.group_id:
        return None
    
    result = await db.execute(
        select(User)
        .where(User.group_id == user.group_id, User.role == UserRole.STUDENT)
        .order_by(User.full_name.asc())
    )
    students = result.scalars().all()
    
    for i, student in enumerate(students):
        if student.id == user.id:
            return i + 1
    return None


async def _check_lab_availability(db: AsyncSession, user_id: UUID, lab: Lab) -> bool:
    """Проверить доступность лабы."""
    if lab.number == 1 or not lab.is_sequential:
        return True
    
    prev_lab_result = await db.execute(
        select(Lab).where(
            Lab.subject_id == lab.subject_id,
            Lab.number == lab.number - 1,
        )
    )
    prev_lab = prev_lab_result.scalar_one_or_none()
    
    if not prev_lab:
        return True
    
    prev_sub_result = await db.execute(
        select(Submission).where(
            Submission.user_id == user_id,
            Submission.lab_id == prev_lab.id,
            Submission.status == SubmissionStatus.ACCEPTED,
        )
    )
    return prev_sub_result.scalar_one_or_none() is not None
