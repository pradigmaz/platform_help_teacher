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
from app.models import User, Lab
from app.schemas.lab import LabCreate, LabUpdate, LabOut, LabDetailResponse, PublishLabResponse
from app.schemas.deadline_extension import (
    DeadlineExtensionCreate, DeadlineExtensionUpdate, 
    DeadlineExtensionResponse, DeadlineExtensionListResponse
)
from app.services.lab_service import lab_service
from app.services.lab_settings_service import lab_settings_service
from app.services.lab_deadline_service import lab_deadline_service
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
    settings = await lab_settings_service.get_lab_settings(db)
    
    if not settings:
        # Возвращаем дефолтные значения без сохранения, is_configured=False
        return schemas.LabSettingsResponse(
            labs_count=10,
            grading_scale="10",
            default_max_grade=10,
            is_configured=False,
        )
    
    return settings


@router.patch("/lab-settings", response_model=schemas.LabSettingsResponse)
async def update_lab_settings(
    settings_in: schemas.LabSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить глобальные настройки лабораторных."""
    settings = await lab_settings_service.update_lab_settings(db, settings_in)
    return settings



# --- Deadline Extensions ---

@router.get("/deadline-extensions", response_model=DeadlineExtensionListResponse)
async def get_deadline_extensions(
    lab_id: Optional[UUID] = Query(default=None),
    group_id: Optional[UUID] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить список продлений дедлайнов."""
    extensions = await lab_deadline_service.get_deadline_extensions(db, lab_id, group_id, is_active)
    
    # Формируем ответ с данными из eager-loaded relationships
    items = []
    for ext in extensions:
        items.append(DeadlineExtensionResponse(
            id=ext.id,
            lab_id=ext.lab_id,
            group_id=ext.group_id,
            bonus_lessons=ext.bonus_lessons,
            reason=ext.reason,
            expires_at=ext.expires_at,
            is_active=ext.is_active,
            created_by=ext.created_by,
            created_at=ext.created_at,
            updated_at=ext.updated_at,
            lab_number=ext.lab.number if ext.lab else None,
            lab_title=ext.lab.title if ext.lab else None,
            group_name=ext.group.name if ext.group else None,
            creator_name=ext.creator.full_name if ext.creator else None,
        ))
    
    return DeadlineExtensionListResponse(items=items, total=len(items))


@router.post("/deadline-extensions", response_model=DeadlineExtensionResponse)
async def create_deadline_extension(
    ext_in: DeadlineExtensionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Создать продление дедлайна для группы."""
    try:
        extension = await lab_deadline_service.create_deadline_extension(db, ext_in, current_user.id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        elif "already exists" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    
    return DeadlineExtensionResponse(
        id=extension.id,
        lab_id=extension.lab_id,
        group_id=extension.group_id,
        bonus_lessons=extension.bonus_lessons,
        reason=extension.reason,
        expires_at=extension.expires_at,
        is_active=extension.is_active,
        created_by=extension.created_by,
        created_at=extension.created_at,
        updated_at=extension.updated_at,
        lab_number=extension.lab.number if extension.lab else None,
        lab_title=extension.lab.title if extension.lab else None,
        group_name=extension.group.name if extension.group else None,
        creator_name=extension.creator.full_name if extension.creator else None,
    )


@router.patch("/deadline-extensions/{extension_id}", response_model=DeadlineExtensionResponse)
async def update_deadline_extension(
    extension_id: UUID,
    ext_in: DeadlineExtensionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить продление дедлайна."""
    extension = await lab_deadline_service.get_deadline_extension_by_id(db, extension_id)
    if not extension:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    extension = await lab_deadline_service.update_deadline_extension(db, extension, ext_in)
    
    return DeadlineExtensionResponse(
        id=extension.id,
        lab_id=extension.lab_id,
        group_id=extension.group_id,
        bonus_lessons=extension.bonus_lessons,
        reason=extension.reason,
        expires_at=extension.expires_at,
        is_active=extension.is_active,
        created_by=extension.created_by,
        created_at=extension.created_at,
        updated_at=extension.updated_at,
        lab_number=extension.lab.number if extension.lab else None,
        lab_title=extension.lab.title if extension.lab else None,
        group_name=extension.group.name if extension.group else None,
        creator_name=extension.creator.full_name if extension.creator else None,
    )


@router.delete("/deadline-extensions/{extension_id}")
async def delete_deadline_extension(
    extension_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Удалить продление дедлайна."""
    extension = await lab_deadline_service.get_deadline_extension_by_id(db, extension_id)
    if not extension:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    await lab_deadline_service.delete_deadline_extension(db, extension)
    
    return {"status": "deleted"}
