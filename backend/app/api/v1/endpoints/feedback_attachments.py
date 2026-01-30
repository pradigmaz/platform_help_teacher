import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.core.limiter import limiter
from app.models import User
from app.models.feedback import Feedback
from app.models.feedback_attachment import FeedbackAttachment
from app.schemas.feedback import UploadUrlResponse
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


@router.post("/{feedback_id}/attachments", response_model=UploadUrlResponse)
@limiter.limit("20/hour")
async def create_attachment_upload_url(
    _request: Request,
    feedback_id: UUID,
    filename: str = Query(..., max_length=255),
    content_type: str = Query(...),
    size: int = Query(..., gt=0, le=MAX_FILE_SIZE),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get presigned URL to upload attachment. Rate limited: 20/hour."""
    logger.info(
        f"[Feedback] Creating attachment for feedback {feedback_id} by user {current_user.id}: filename={filename}, type={content_type}, size={size}"
    )

    if content_type not in ALLOWED_TYPES:
        logger.warning(
            f"[Feedback] Invalid content type for feedback {feedback_id}: {content_type}"
        )
        raise HTTPException(
            400,
            f"Тип файла '{content_type}' не поддерживается. Разрешены: {', '.join(ALLOWED_TYPES)}",
        )

    ext = _validate_extension(filename)
    logger.debug(f"[Feedback] Validated extension for {filename}: {ext}")

    result = await db.execute(
        select(Feedback)
        .options(selectinload(Feedback.attachments))
        .where(Feedback.id == feedback_id, Feedback.user_id == current_user.id)
    )
    feedback = result.scalar_one_or_none()
    if not feedback:
        logger.warning(
            f"[Feedback] Feedback {feedback_id} not found or not owned by user {current_user.id}"
        )
        raise HTTPException(404, "Фидбэк не найден")

    current_count = len(feedback.attachments)
    logger.debug(
        f"[Feedback] Current attachment count for feedback {feedback_id}: {current_count}/{MAX_ATTACHMENTS}"
    )
    if current_count >= MAX_ATTACHMENTS:
        logger.warning(
            f"[Feedback] Attachment limit reached for feedback {feedback_id}: {current_count} >= {MAX_ATTACHMENTS}"
        )
        raise HTTPException(400, f"Максимум {MAX_ATTACHMENTS} вложений")

    attachment_id = uuid4()
    storage_path = f"feedback/{feedback_id}/{attachment_id}.{ext}"
    logger.debug(f"[Feedback] Generated storage path: {storage_path}")

    storage = StorageService()
    try:
        upload_url = await storage.create_presigned_upload_url(
            storage_path, content_type
        )
        logger.info(f"[Feedback] Presigned URL created for attachment {attachment_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[Feedback] Failed to create presigned URL for {attachment_id}: {e}"
        )
        raise HTTPException(500, "Не удалось создать ссылку для загрузки")

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
    await db.refresh(attachment)
    logger.info(
        f"[Feedback] Attachment record created successfully: {attachment_id} (is_uploaded={attachment.is_uploaded})"
    )

    return UploadUrlResponse(
        upload_url=upload_url, attachment_id=attachment_id, storage_path=storage_path
    )


@router.post("/{feedback_id}/attachments/{attachment_id}/presign")
@limiter.limit("30/hour")
async def get_presigned_url_for_attachment(
    _request: Request,
    feedback_id: UUID,
    attachment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get presigned upload URL for existing attachment (for retry).
    This endpoint allows reusing the same attachment_id on retry.
    Rate limited: 30/hour.
    """
    logger.info(
        f"[Feedback] Getting presigned URL for retry: feedback={feedback_id}, attachment={attachment_id}, user={current_user.id}"
    )

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
        logger.warning(
            f"[Feedback] Attachment {attachment_id} not found or not owned by user {current_user.id}"
        )
        raise HTTPException(404, "Вложение не найдено")

    logger.debug(
        f"[Feedback] Attachment found: filename={attachment.filename}, is_uploaded={attachment.is_uploaded}, content_type={attachment.content_type}"
    )

    storage = StorageService()
    try:
        upload_url = await storage.create_presigned_upload_url(
            attachment.storage_path, attachment.content_type
        )
        logger.info(
            f"[Feedback] Presigned URL regenerated for attachment {attachment_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[Feedback] Failed to regenerate presigned URL for {attachment_id}: {e}"
        )
        raise HTTPException(500, "Не удалось создать ссылку для загрузки")

    return UploadUrlResponse(
        upload_url=upload_url,
        attachment_id=attachment_id,
        storage_path=attachment.storage_path,
    )


@router.put("/{feedback_id}/attachments/{attachment_id}/mark-uploaded")
@limiter.limit("30/hour")
async def mark_attachment_uploaded(
    _request: Request,
    feedback_id: UUID,
    attachment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark attachment as successfully uploaded.
    This helps distinguish between stale attachments (DB record exists but file not uploaded)
    and successfully uploaded attachments.
    Rate limited: 30/hour.
    """
    logger.info(
        f"[Feedback] Marking attachment {attachment_id} as uploaded for feedback {feedback_id}"
    )

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
        logger.warning(
            f"[Feedback] Attachment {attachment_id} not found or not owned by user {current_user.id}"
        )
        raise HTTPException(404, "Вложение не найдено")

    try:
        storage = StorageService()
        async with storage.get_client() as client:
            await client.head_object(Bucket=storage.bucket, Key=attachment.storage_path)
            logger.info(
                f"[Feedback] Verified file exists in storage: {attachment.storage_path}"
            )
    except Exception as e:
        logger.error(
            f"[Feedback] Failed to verify file in storage for attachment {attachment_id}: {e}"
        )
        raise HTTPException(
            400, "Файл не найден в хранилище. Попробуйте загрузить снова."
        )

    attachment.is_uploaded = True
    attachment.uploaded_at = datetime.now(timezone.utc)
    await db.commit()
    logger.info(
        f"[Feedback] Attachment {attachment_id} marked as uploaded successfully at {attachment.uploaded_at}"
    )

    return {"status": "uploaded", "attachment_id": str(attachment_id)}


@router.get("/{feedback_id}/attachments/{attachment_id}/url")
async def get_attachment_url(
    feedback_id: UUID,
    attachment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get presigned download URL for attachment. Only owner or admin can access."""
    is_admin = current_user.role.value == "admin"

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
    logger.info(
        f"[Feedback] Deleting attachment {attachment_id} from feedback {feedback_id}"
    )

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
        logger.warning(f"[Feedback] Attachment {attachment_id} not found for deletion")
        raise HTTPException(404, "Вложение не найдено")

    storage = StorageService()
    try:
        await storage.delete_object(attachment.storage_path)
        logger.info(f"[Feedback] Deleted attachment {attachment_id} from storage")
    except Exception as e:
        logger.warning(
            f"[Feedback] Failed to delete attachment {attachment_id} from storage: {e}"
        )

    await db.delete(attachment)
    await db.commit()
    logger.info(f"[Feedback] Attachment {attachment_id} record deleted from database")
    return {"ok": True}
