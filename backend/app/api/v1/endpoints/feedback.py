"""Feedback endpoints for bug reports and suggestions."""
import logging
from typing import List
from uuid import UUID, uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.api.deps import get_db, get_current_user, get_current_active_superuser
from app.core.limiter import limiter
from app.models import User
from app.models.feedback import Feedback, FeedbackStatus
from app.models.feedback_attachment import FeedbackAttachment
from app.schemas.feedback import (
    FeedbackCreate, FeedbackResponse, FeedbackUpdate,
    UploadUrlResponse, FeedbackAttachmentResponse
)
from app.services.storage import StorageService

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_ATTACHMENTS = 5
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _validate_extension(filename: str) -> str:
    """Validate and return file extension."""
    if "." not in filename:
        raise HTTPException(400, "Файл должен иметь расширение")
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Расширение .{ext} не поддерживается")
    return ext


def _build_response(feedback: Feedback, user_name: str = None, group_name: str = None) -> FeedbackResponse:
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


@router.post("/{feedback_id}/attachments", response_model=UploadUrlResponse)
@limiter.limit("20/hour")
async def create_attachment_upload_url(
    request: Request,
    feedback_id: UUID,
    filename: str = Query(..., max_length=255),
    content_type: str = Query(...),
    size: int = Query(..., gt=0, le=MAX_FILE_SIZE),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get presigned URL to upload attachment. Rate limited: 20/hour."""
    # Validate content type
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Тип файла не поддерживается. Разрешены: {', '.join(ALLOWED_TYPES)}")
    
    # Validate extension
    ext = _validate_extension(filename)
    
    # Check feedback exists and belongs to user
    result = await db.execute(
        select(Feedback)
        .options(selectinload(Feedback.attachments))
        .where(Feedback.id == feedback_id, Feedback.user_id == current_user.id)
    )
    feedback = result.scalar_one_or_none()
    if not feedback:
        raise HTTPException(404, "Фидбэк не найден")
    
    # Check attachment limit
    if len(feedback.attachments) >= MAX_ATTACHMENTS:
        raise HTTPException(400, f"Максимум {MAX_ATTACHMENTS} вложений")
    
    # Generate storage path with validated extension
    attachment_id = uuid4()
    storage_path = f"feedback/{feedback_id}/{attachment_id}.{ext}"
    
    # Generate presigned URL first (before creating DB record)
    storage = StorageService()
    try:
        upload_url = await storage.create_presigned_upload_url(storage_path, content_type)
    except Exception as e:
        logger.error(f"Failed to create presigned URL: {e}")
        raise HTTPException(500, "Не удалось создать ссылку для загрузки")
    
    # Create attachment record only after URL is generated
    attachment = FeedbackAttachment(
        id=attachment_id,
        feedback_id=feedback_id,
        filename=filename,
        storage_path=storage_path,
        content_type=content_type,
        size=size,
    )
    db.add(attachment)
    await db.commit()
    
    return UploadUrlResponse(upload_url=upload_url, attachment_id=attachment_id, storage_path=storage_path)


@router.get("/{feedback_id}/attachments/{attachment_id}/url")
async def get_attachment_url(
    feedback_id: UUID,
    attachment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get presigned download URL for attachment. Only owner or admin can access."""
    # Check if user is admin
    is_admin = current_user.role.value == "admin"
    
    # Build query with ownership check for non-admins
    query = (
        select(FeedbackAttachment)
        .join(Feedback)
        .where(
            FeedbackAttachment.id == attachment_id,
            FeedbackAttachment.feedback_id == feedback_id,
        )
    )
    
    if not is_admin:
        query = query.where(Feedback.user_id == current_user.id)
    
    result = await db.execute(query)
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise HTTPException(404, "Вложение не найдено")
    
    storage = StorageService()
    url = await storage.create_presigned_download_url(attachment.storage_path)
    return {"url": url}


@router.delete("/{feedback_id}/attachments/{attachment_id}")
async def delete_attachment(
    feedback_id: UUID,
    attachment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete attachment (owner only)."""
    result = await db.execute(
        select(FeedbackAttachment)
        .join(Feedback)
        .where(
            FeedbackAttachment.id == attachment_id,
            FeedbackAttachment.feedback_id == feedback_id,
            Feedback.user_id == current_user.id,
        )
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise HTTPException(404, "Вложение не найдено")
    
    # Delete from storage
    storage = StorageService()
    try:
        await storage.delete_object(attachment.storage_path)
    except Exception as e:
        logger.warning(f"Failed to delete attachment from storage: {e}")
    
    await db.delete(attachment)
    await db.commit()
    return {"ok": True}


@router.get("/count/new")
async def get_new_feedback_count(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
):
    """Get count of new (unread) feedback."""
    result = await db.execute(
        select(func.count(Feedback.id)).where(Feedback.status == FeedbackStatus.NEW)
    )
    return {"count": result.scalar() or 0}


@router.get("", response_model=List[FeedbackResponse])
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
            feedback.resolved_at = datetime.now(timezone.utc)
    
    if data.admin_response is not None:
        feedback.admin_response = data.admin_response
    
    await db.commit()
    await db.refresh(feedback)
    return _build_response(feedback)
