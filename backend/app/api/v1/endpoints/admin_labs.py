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
from app.models.lab_deadline_extension import LabDeadlineExtension
from app.models.group import Group
from app.schemas.lab import LabCreate, LabUpdate, LabOut, LabDetailResponse, PublishLabResponse
from app.schemas.deadline_extension import (
    DeadlineExtensionCreate, DeadlineExtensionUpdate, 
    DeadlineExtensionResponse, DeadlineExtensionListResponse
)
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
    query = select(LabDeadlineExtension)
    
    if lab_id:
        query = query.where(LabDeadlineExtension.lab_id == lab_id)
    if group_id:
        query = query.where(LabDeadlineExtension.group_id == group_id)
    if is_active is not None:
        query = query.where(LabDeadlineExtension.is_active == is_active)
    
    query = query.order_by(LabDeadlineExtension.created_at.desc())
    result = await db.execute(query)
    extensions = result.scalars().all()
    
    # Загружаем связанные данные для отображения
    items = []
    for ext in extensions:
        lab = await db.get(Lab, ext.lab_id)
        group = await db.get(Group, ext.group_id)
        creator = await db.get(User, ext.created_by) if ext.created_by else None
        
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
            lab_number=lab.number if lab else None,
            lab_title=lab.title if lab else None,
            group_name=group.name if group else None,
            creator_name=creator.full_name if creator else None,
        ))
    
    return DeadlineExtensionListResponse(items=items, total=len(items))


@router.post("/deadline-extensions", response_model=DeadlineExtensionResponse)
async def create_deadline_extension(
    ext_in: DeadlineExtensionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Создать продление дедлайна для группы."""
    # Проверяем существование лабы и группы
    lab = await db.get(Lab, ext_in.lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    
    group = await db.get(Group, ext_in.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Проверяем нет ли уже активного продления
    existing = await db.execute(
        select(LabDeadlineExtension).where(
            LabDeadlineExtension.lab_id == ext_in.lab_id,
            LabDeadlineExtension.group_id == ext_in.group_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Extension already exists for this lab and group")
    
    extension = LabDeadlineExtension(
        lab_id=ext_in.lab_id,
        group_id=ext_in.group_id,
        bonus_lessons=ext_in.bonus_lessons,
        reason=ext_in.reason,
        expires_at=ext_in.expires_at,
        created_by=current_user.id,
    )
    db.add(extension)
    await db.commit()
    await db.refresh(extension)
    
    logger.info(f"Created deadline extension for lab {lab.number} group {group.name}: +{ext_in.bonus_lessons} lessons")
    
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
        lab_number=lab.number,
        lab_title=lab.title,
        group_name=group.name,
        creator_name=current_user.full_name,
    )


@router.patch("/deadline-extensions/{extension_id}", response_model=DeadlineExtensionResponse)
async def update_deadline_extension(
    extension_id: UUID,
    ext_in: DeadlineExtensionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить продление дедлайна."""
    extension = await db.get(LabDeadlineExtension, extension_id)
    if not extension:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    update_data = ext_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(extension, field, value)
    
    await db.commit()
    await db.refresh(extension)
    
    lab = await db.get(Lab, extension.lab_id)
    group = await db.get(Group, extension.group_id)
    creator = await db.get(User, extension.created_by) if extension.created_by else None
    
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
        lab_number=lab.number if lab else None,
        lab_title=lab.title if lab else None,
        group_name=group.name if group else None,
        creator_name=creator.full_name if creator else None,
    )


@router.delete("/deadline-extensions/{extension_id}")
async def delete_deadline_extension(
    extension_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Удалить продление дедлайна."""
    extension = await db.get(LabDeadlineExtension, extension_id)
    if not extension:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    await db.delete(extension)
    await db.commit()
    
    return {"status": "deleted"}
