"""API endpoints для объявлений (админ)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud.crud_announcement import crud_announcement
from app.db.session import get_db
from app.models.user import User
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementListResponse,
    AnnouncementResponse,
    AnnouncementUpdate,
)
from app.services.announcement_service import send_announcement_to_students

router = APIRouter()


@router.get("/", response_model=list[AnnouncementListResponse])
async def get_announcements(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить все объявления (черновики + опубликованные)."""
    announcements = await crud_announcement.get_all(db, skip=skip, limit=limit)
    return [AnnouncementListResponse.model_validate(a) for a in announcements]


@router.post("/", response_model=AnnouncementResponse)
async def create_announcement(
    data: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
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


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить объявление по ID."""
    announcement = await crud_announcement.get(db, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return _to_response(announcement)


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: UUID,
    data: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить объявление."""
    announcement = await crud_announcement.get(db, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    announcement = await crud_announcement.update(db, announcement, title=data.title, content=data.content)
    return _to_response(announcement)


@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Удалить объявление."""
    deleted = await crud_announcement.delete(db, announcement_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return {"status": "deleted"}


@router.post("/{announcement_id}/publish", response_model=AnnouncementResponse)
async def publish_announcement(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Опубликовать объявление."""
    announcement = await crud_announcement.get(db, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    if not announcement.is_draft:
        raise HTTPException(status_code=400, detail="Объявление уже опубликовано")

    announcement = await crud_announcement.publish(db, announcement)
    return _to_response(announcement)


@router.post("/{announcement_id}/send")
async def send_announcement(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Отправить объявление студентам через ботов."""
    announcement = await crud_announcement.get(db, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    if announcement.is_draft:
        raise HTTPException(status_code=400, detail="Сначала опубликуйте объявление")

    stats = await send_announcement_to_students(db, announcement)
    return {"status": "sent", "stats": stats}


def _to_response(announcement) -> AnnouncementResponse:
    """Конвертировать в response с author_name."""
    return AnnouncementResponse(
        id=announcement.id,
        title=announcement.title,
        content=announcement.content,
        created_by=announcement.created_by,
        author_name=announcement.author.full_name if announcement.author else None,
        is_draft=announcement.is_draft,
        published_at=announcement.published_at,
        created_at=announcement.created_at,
        updated_at=announcement.updated_at,
    )
