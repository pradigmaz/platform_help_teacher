"""
Feedback endpoints for bug reports and suggestions.

Attachment upload endpoints are defined in feedback_attachments.py to keep this
module focused on feedback CRUD operations.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.api.deps import get_current_active_superuser, get_current_user, get_db
from app.core.limiter import limiter
from app.models import User
from app.models.feedback import Feedback, FeedbackStatus
from app.schemas.feedback import (
    FeedbackAttachmentResponse,
    FeedbackCreate,
    FeedbackResponse,
    FeedbackUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_response(
    feedback: Feedback, user_name: str | None = None, group_name: str | None = None
) -> FeedbackResponse:
    """Build FeedbackResponse from model."""
    return FeedbackResponse(
        id=feedback.id,
        type=feedback.type,
        title=feedback.title,
        description=feedback.description,
        status=feedback.status,
        user_id=feedback.user_id,
        user_name=user_name or (feedback.user.full_name if feedback.user else None),
        group_name=group_name or (feedback.user.group.name if feedback.user and feedback.user.group else None),
        admin_response=feedback.admin_response,
        attachments=[FeedbackAttachmentResponse.model_validate(a) for a in (feedback.attachments or [])],
        created_at=feedback.created_at,
        resolved_at=feedback.resolved_at,
    )


@router.post("", response_model=FeedbackResponse)
@limiter.limit("5/hour")
async def create_feedback(
    request: Request,
    data: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit feedback (bug report or suggestion). Rate limited: 5/hour."""
    feedback = Feedback(
        type=data.type,
        title=data.title,
        description=data.description,
        user_id=current_user.id,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    group_name = None
    if current_user.group_id:
        from app.models.group import Group

        result = await db.execute(select(Group.name).where(Group.id == current_user.group_id))
        group_name = result.scalar_one_or_none()

    logger.info(f"Feedback created: {feedback.id} by user {current_user.id}")
    return _build_response(feedback, current_user.full_name, group_name)


@router.get("/count/new")
async def get_new_feedback_count(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
):
    """Get count of new (unread) feedback."""
    result = await db.execute(select(func.count(Feedback.id)).where(Feedback.status == FeedbackStatus.NEW))
    return {"count": result.scalar() or 0}


@router.get("", response_model=list[FeedbackResponse])
async def list_feedback(
    status: FeedbackStatus | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
):
    """List all feedback (admin only) with pagination."""
    query = (
        select(Feedback)
        .options(
            joinedload(Feedback.user).selectinload(User.group),
            selectinload(Feedback.attachments),
        )
        .order_by(Feedback.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if status:
        query = query.where(Feedback.status == status)

    result = await db.execute(query)
    feedbacks = result.scalars().unique().all()
    return [_build_response(f) for f in feedbacks]


@router.patch("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: UUID,
    data: FeedbackUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
):
    """Update feedback status/response (admin only)."""
    result = await db.execute(
        select(Feedback)
        .options(
            joinedload(Feedback.user).selectinload(User.group),
            selectinload(Feedback.attachments),
        )
        .where(Feedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()

    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    if data.status:
        feedback.status = data.status
        if data.status in (FeedbackStatus.RESOLVED, FeedbackStatus.CLOSED):
            feedback.resolved_at = datetime.now(UTC)

    if data.admin_response is not None:
        feedback.admin_response = data.admin_response

    await db.commit()
    await db.refresh(feedback)
    return _build_response(feedback)
