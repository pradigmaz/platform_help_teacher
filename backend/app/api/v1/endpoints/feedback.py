"""Feedback endpoints for bug reports and suggestions."""
import logging
from typing import List
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import get_db, get_current_user, get_current_active_superuser
from app.models import User
from app.models.feedback import Feedback, FeedbackStatus
from app.schemas.feedback import FeedbackCreate, FeedbackResponse, FeedbackUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=FeedbackResponse)
async def create_feedback(
    data: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit feedback (bug report or suggestion)."""
    feedback = Feedback(
        type=data.type,
        title=data.title,
        description=data.description,
        user_id=current_user.id,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    
    logger.info(f"Feedback created: {feedback.id} by user {current_user.id}")
    
    return FeedbackResponse(
        id=feedback.id,
        type=feedback.type,
        title=feedback.title,
        description=feedback.description,
        status=feedback.status,
        user_id=feedback.user_id,
        user_name=current_user.full_name,
        admin_response=feedback.admin_response,
        created_at=feedback.created_at,
        resolved_at=feedback.resolved_at,
    )


@router.get("", response_model=List[FeedbackResponse])
async def list_feedback(
    status: FeedbackStatus | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
):
    """List all feedback (admin only)."""
    query = select(Feedback).options(joinedload(Feedback.user)).order_by(Feedback.created_at.desc())
    
    if status:
        query = query.where(Feedback.status == status)
    
    result = await db.execute(query)
    feedbacks = result.scalars().all()
    
    return [
        FeedbackResponse(
            id=f.id,
            type=f.type,
            title=f.title,
            description=f.description,
            status=f.status,
            user_id=f.user_id,
            user_name=f.user.full_name if f.user else None,
            admin_response=f.admin_response,
            created_at=f.created_at,
            resolved_at=f.resolved_at,
        )
        for f in feedbacks
    ]


@router.patch("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: UUID,
    data: FeedbackUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
):
    """Update feedback status/response (admin only)."""
    result = await db.execute(
        select(Feedback).options(joinedload(Feedback.user)).where(Feedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    if data.status:
        feedback.status = data.status
        if data.status in (FeedbackStatus.RESOLVED, FeedbackStatus.CLOSED):
            feedback.resolved_at = datetime.now(timezone.utc)
    
    if data.admin_response is not None:
        feedback.admin_response = data.admin_response
    
    await db.commit()
    await db.refresh(feedback)
    
    return FeedbackResponse(
        id=feedback.id,
        type=feedback.type,
        title=feedback.title,
        description=feedback.description,
        status=feedback.status,
        user_id=feedback.user_id,
        user_name=feedback.user.full_name if feedback.user else None,
        admin_response=feedback.admin_response,
        created_at=feedback.created_at,
        resolved_at=feedback.resolved_at,
    )
