"""API endpoints для объявлений (админ)."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud.crud_announcement import crud_announcement
from app.db.session import get_db
from app.models.announcement import Announcement, AnnouncementSendStatus
from app.models.user import User
from app.schemas.announcement import (
    AdminAnnouncementListResponse,
    AdminAnnouncementResponse,
    AnnouncementCreate,
    AnnouncementDeliveryStats,
    AnnouncementUpdate,
)
from app.tasks.announcement_tasks import send_announcement_task

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=list[AdminAnnouncementListResponse])
async def get_announcements(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
):
    """Получить все объявления (черновики + опубликованные)."""
    announcements = await crud_announcement.get_all(db, skip=skip, limit=limit)
    return [_to_list_response(announcement) for announcement in announcements]


@router.post("/", response_model=AdminAnnouncementResponse)
async def create_announcement(
    data: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
):
    """Создать черновик объявления."""
    announcement = await crud_announcement.create(
        db, title=data.title, content=data.content, created_by=current_user.id
    )
    # Reload with author
    reloaded_announcement = await crud_announcement.get(db, announcement.id)
    if reloaded_announcement is None:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return _to_response(reloaded_announcement)


@router.get("/{announcement_id}", response_model=AdminAnnouncementResponse)
async def get_announcement(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
):
    """Получить объявление по ID."""
    announcement = await crud_announcement.get(db, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return _to_response(announcement)


@router.put("/{announcement_id}", response_model=AdminAnnouncementResponse)
async def update_announcement(
    announcement_id: UUID,
    data: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
):
    """Обновить объявление."""
    announcement = await crud_announcement.get(db, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    if announcement.send_status is AnnouncementSendStatus.SENT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Отправленное объявление нельзя редактировать")

    announcement = await crud_announcement.update(db, announcement, title=data.title, content=data.content)
    return _to_response(announcement)


@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
):
    """Удалить объявление."""
    announcement = await crud_announcement.get(db, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    if not announcement.is_draft:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Можно удалять только черновики")

    deleted = await crud_announcement.delete(db, announcement_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return {"status": "deleted"}


@router.post("/{announcement_id}/publish", response_model=AdminAnnouncementResponse)
async def publish_announcement(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
):
    """Опубликовать объявление."""
    announcement = await crud_announcement.get(db, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    if not announcement.is_draft:
        raise HTTPException(status_code=400, detail="Объявление уже опубликовано")

    announcement = await crud_announcement.publish(db, announcement)
    logger.info("announcement_published announcement_id=%s actor_id=%s", announcement.id, current_user.id)
    return _to_response(announcement)


@router.post(
    "/{announcement_id}/send",
    response_model=AdminAnnouncementResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_announcement(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
):
    """Поставить объявление в очередь на отправку студентам через ботов."""
    announcement = await crud_announcement.get(db, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    if announcement.is_draft:
        raise HTTPException(status_code=400, detail="Сначала опубликуйте объявление")
    if announcement.send_status is AnnouncementSendStatus.SENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Объявление уже отправляется")
    if announcement.send_status is AnnouncementSendStatus.SENT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Объявление уже отправлено")

    announcement = await crud_announcement.mark_send_enqueued(db, announcement, current_user.id)
    try:
        send_announcement_task.delay(str(announcement.id))
    except Exception as exc:
        logger.exception("announcement_send_enqueue_failed announcement_id=%s", announcement.id)
        announcement = await crud_announcement.mark_send_enqueue_failed(db, announcement, current_user.id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Не удалось запустить отправку"
        ) from exc

    logger.info("announcement_send_enqueued announcement_id=%s actor_id=%s", announcement.id, current_user.id)
    return _to_response(announcement)


def _to_list_response(announcement: Announcement) -> AdminAnnouncementListResponse:
    delivery_stats = None
    if announcement.delivery_stats is not None:
        delivery_stats = AnnouncementDeliveryStats.model_validate(announcement.delivery_stats)

    return AdminAnnouncementListResponse(
        id=announcement.id,
        title=announcement.title,
        content=announcement.content,
        author_name=announcement.author.full_name if announcement.author else None,
        is_draft=announcement.is_draft,
        send_status=announcement.send_status,
        published_at=announcement.published_at,
        send_started_at=announcement.send_started_at,
        sent_at=announcement.sent_at,
        created_at=announcement.created_at,
        updated_at=announcement.updated_at,
        delivery_stats=delivery_stats,
        delivery_error=announcement.delivery_error,
    )


def _to_response(announcement: Announcement) -> AdminAnnouncementResponse:
    """Конвертировать в admin response с author_name и статусом доставки."""
    return AdminAnnouncementResponse(
        **_to_list_response(announcement).model_dump(),
        created_by=announcement.created_by,
        sent_by=announcement.sent_by,
    )
