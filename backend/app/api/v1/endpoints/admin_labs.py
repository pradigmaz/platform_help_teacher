from typing import List, Optional
from uuid import UUID
import logging
import json

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.core.limiter import limiter
from app.core.redis import get_redis
from app.core.constants import RATE_LIMIT_LAB_CREATE, RATE_LIMIT_LAB_DELETE, RATE_LIMIT_LAB_PUBLISH
from app.models import User, Lab, LabSettings
from app.schemas.lab import LabCreate, LabUpdate, LabOut, LabDetailResponse, PublishLabResponse
from app.services.lab_service import lab_service
from app import schemas

router = APIRouter()
logger = logging.getLogger(__name__)

# Константы кэширования
LABS_CACHE_PREFIX = "labs:list"
LABS_CACHE_TTL = 300  # 5 минут


def _get_labs_cache_key(subject_id: Optional[UUID], skip: int, limit: int) -> str:
    """Генерация ключа кэша для списка лаб."""
    subject_key = str(subject_id) if subject_id else "all"
    return f"{LABS_CACHE_PREFIX}:{subject_key}:{skip}:{limit}"


async def _invalidate_labs_cache() -> None:
    """Инвалидация всего кэша списка лаб."""
    try:
        redis = await get_redis()
        if redis:
            # Удаляем все ключи по паттерну
            keys = await redis.keys(f"{LABS_CACHE_PREFIX}:*")
            if keys:
                await redis.delete(*keys)
                logger.debug(f"Invalidated {len(keys)} labs cache keys")
    except Exception as e:
        logger.warning(f"Redis labs cache invalidation error: {e}")


@router.get("/labs", response_model=List[LabOut])
async def get_all_labs(
    skip: int = Query(default=0, ge=0, description="Пропустить записей"),
    limit: int = Query(default=100, ge=1, le=500, description="Лимит записей"),
    subject_id: Optional[UUID] = Query(default=None, description="Фильтр по предмету"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить все лабораторные работы с пагинацией (с кэшированием)."""
    cache_key = _get_labs_cache_key(subject_id, skip, limit)
    
    # Пробуем получить из кэша
    try:
        redis = await get_redis()
        if redis:
            cached = await redis.get(cache_key)
            if cached:
                logger.debug(f"Labs cache hit: {cache_key}")
                return json.loads(cached)
    except Exception as e:
        logger.warning(f"Redis labs cache read error: {e}")
    
    # Запрос к БД
    query = select(Lab).where(Lab.deleted_at.is_(None))
    
    if subject_id:
        query = query.where(Lab.subject_id == subject_id)
    
    query = query.order_by(Lab.number.asc(), Lab.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    labs = result.scalars().all()
    
    # Сериализуем и кэшируем
    labs_data = [LabOut.model_validate(lab).model_dump(mode='json') for lab in labs]
    
    try:
        redis = await get_redis()
        if redis:
            await redis.setex(cache_key, LABS_CACHE_TTL, json.dumps(labs_data))
            logger.debug(f"Labs cached: {cache_key}")
    except Exception as e:
        logger.warning(f"Redis labs cache write error: {e}")
    
    return labs


@router.get("/labs/{lab_id}", response_model=LabDetailResponse)
async def get_lab(
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> LabDetailResponse:
    """Получить одну лабораторную работу."""
    lab = await lab_service.get_by_id(db, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    return LabDetailResponse.model_validate(lab)


@router.post("/labs", response_model=LabOut)
@limiter.limit(RATE_LIMIT_LAB_CREATE)
async def create_lab(
    request: Request,
    lab_in: LabCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Создать лабораторную работу."""
    lab = await lab_service.create(db, lab_in)
    await _invalidate_labs_cache()
    return lab


@router.patch("/labs/{lab_id}", response_model=LabOut)
async def update_lab(
    lab_id: UUID,
    lab_in: LabUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить лабораторную работу."""
    lab = await lab_service.get_by_id(db, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    lab = await lab_service.update(db, lab, lab_in)
    await _invalidate_labs_cache()
    return lab


@router.delete("/labs/{lab_id}", response_model=schemas.DeleteResponse)
@limiter.limit(RATE_LIMIT_LAB_DELETE)
async def delete_lab(
    request: Request,
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> schemas.DeleteResponse:
    """Soft-delete лабораторной работы."""
    lab = await lab_service.get_by_id(db, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    await lab_service.soft_delete(db, lab)
    await _invalidate_labs_cache()
    return {"status": "deleted"}


@router.post("/labs/{lab_id}/publish", response_model=PublishLabResponse)
@limiter.limit(RATE_LIMIT_LAB_PUBLISH)
async def publish_lab(
    request: Request,
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> PublishLabResponse:
    """Опубликовать лабораторную работу."""
    lab = await lab_service.get_by_id(db, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    
    if lab.is_published:
        return PublishLabResponse(status="already_published", public_code=lab.public_code)
    
    try:
        code = await lab_service.publish(db, lab)
        await _invalidate_labs_cache()
        return PublishLabResponse(status="published", public_code=code)
    except ValueError as e:
        logger.error(f"Failed to publish lab {lab_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate unique code")


@router.post("/labs/{lab_id}/unpublish", response_model=PublishLabResponse)
async def unpublish_lab(
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> PublishLabResponse:
    """Снять лабораторную с публикации."""
    lab = await lab_service.get_by_id(db, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    await lab_service.unpublish(db, lab)
    await _invalidate_labs_cache()
    return PublishLabResponse(status="unpublished")


# --- Global Lab Settings ---

@router.get("/lab-settings", response_model=schemas.LabSettingsResponse)
async def get_lab_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить глобальные настройки лабораторных."""
    result = await db.execute(select(LabSettings).limit(1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Создаём настройки по умолчанию
        settings = LabSettings(labs_count=10, default_max_grade=10)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return settings


@router.patch("/lab-settings", response_model=schemas.LabSettingsResponse)
async def update_lab_settings(
    settings_in: schemas.LabSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить глобальные настройки лабораторных."""
    result = await db.execute(select(LabSettings).limit(1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = LabSettings(labs_count=10, default_max_grade=10)
        db.add(settings)
        await db.flush()
    
    update_data = settings_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    await db.commit()
    await db.refresh(settings)
    return settings

