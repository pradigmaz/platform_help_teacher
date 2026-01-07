"""API endpoints для лекций (админ)."""
import logging
from typing import List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.crud.crud_lecture import crud_lecture
from app.services.lecture_service import lecture_service
from app.models.user import User
from app.models.lecture_image import LectureImage
from app.schemas.lecture import (
    LectureCreate,
    LectureUpdate,
    LectureResponse,
    LectureListResponse,
    LectureImageResponse,
    PublicLinkResponse,
)
from app.services.pdf_service import pdf_service
from app.services.storage import StorageService
from app.core.config import settings
from app.core.limiter import limiter
from app.core.constants import LECTURE_PDF_TIMEOUT_MS

logger = logging.getLogger(__name__)

router = APIRouter()

# Инициализация StorageService
storage_service = StorageService()

# Допустимые MIME-типы для изображений
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}


@router.get("/", response_model=List[LectureListResponse])
async def get_lectures(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    subject_id: UUID = Query(None, description="Фильтр по предмету"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить список лекций."""
    lectures = await crud_lecture.list_all(db, skip=skip, limit=limit, subject_id=subject_id)
    return lectures


@router.post("/", response_model=LectureResponse)
async def create_lecture(
    lecture_in: LectureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Создать лекцию."""
    lecture = await crud_lecture.create(db, lecture_in)
    return lecture



@router.get("/{lecture_id}", response_model=LectureResponse)
async def get_lecture(
    lecture_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить лекцию по ID."""
    lecture = await crud_lecture.get(db, lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Лекция не найдена")
    return lecture


@router.put("/{lecture_id}", response_model=LectureResponse)
async def update_lecture(
    lecture_id: UUID,
    lecture_in: LectureUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить лекцию."""
    lecture = await crud_lecture.get(db, lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Лекция не найдена")
    
    lecture = await crud_lecture.update(db, lecture, lecture_in)
    return lecture


@router.delete("/{lecture_id}")
async def delete_lecture(
    lecture_id: UUID,
    hard: bool = Query(False, description="Жёсткое удаление"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Удалить лекцию (soft-delete по умолчанию)."""
    lecture = await crud_lecture.get(db, lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Лекция не найдена")
    
    if hard:
        await crud_lecture.delete(db, lecture_id)
    else:
        await lecture_service.soft_delete(db, lecture)
    return {"status": "deleted"}


@router.post("/{lecture_id}/restore")
async def restore_lecture(
    lecture_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Восстановить удалённую лекцию."""
    lecture = await crud_lecture.get(db, lecture_id, include_deleted=True)
    if not lecture:
        raise HTTPException(status_code=404, detail="Лекция не найдена")
    if lecture.deleted_at is None:
        raise HTTPException(status_code=400, detail="Лекция не удалена")
    
    await lecture_service.restore(db, lecture)
    return {"status": "restored"}


@router.post("/{lecture_id}/publish", response_model=PublicLinkResponse)
async def publish_lecture(
    lecture_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Опубликовать лекцию и получить публичную ссылку."""
    lecture = await crud_lecture.get(db, lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Лекция не найдена")
    
    public_code = await lecture_service.publish(db, lecture)
    return PublicLinkResponse(
        public_code=public_code,
        url=f"/lectures/view/{public_code}"
    )


@router.post("/{lecture_id}/unpublish")
async def unpublish_lecture(
    lecture_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Снять лекцию с публикации."""
    lecture = await crud_lecture.get(db, lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Лекция не найдена")
    
    await lecture_service.unpublish(db, lecture)
    return {"status": "unpublished"}


@router.get("/{lecture_id}/pdf")
@limiter.limit("5/minute")
async def export_lecture_pdf(
    request: Request,
    lecture_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Экспорт лекции в PDF.
    Requirements: 6.1
    """
    lecture = await crud_lecture.get(db, lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Лекция не найдена")
    
    try:
        # Хэш updated_at для кэширования
        import hashlib
        updated_at_hash = hashlib.md5(str(lecture.updated_at).encode()).hexdigest()[:8]
        
        pdf_bytes = await pdf_service.generate_pdf(lecture_id, updated_at_hash)
        
        # Формируем имя файла из заголовка лекции
        safe_title = "".join(c for c in lecture.title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_title or 'lecture'}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        logger.error(f"PDF generation failed for lecture {lecture_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Не удалось сгенерировать PDF"
        )


@router.post("/{lecture_id}/images", response_model=LectureImageResponse)
async def upload_lecture_image(
    lecture_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Загрузить изображение для лекции.
    Requirements: 2.5
    """
    # Проверяем существование лекции
    lecture = await crud_lecture.get(db, lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Лекция не найдена")
    
    # Проверяем MIME-тип
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимый тип файла. Разрешены: JPG, PNG, GIF, WebP"
        )
    
    # Читаем содержимое файла
    content = await file.read()
    
    # Проверяем размер
    if len(content) > settings.MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Размер файла превышает 10MB"
        )
    
    # Генерируем уникальный путь для хранения
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    storage_path = f"lectures/{lecture_id}/{uuid4()}.{file_ext}"
    
    try:
        # Получаем presigned URL для загрузки
        upload_url = await storage_service.create_presigned_upload_url(
            storage_path,
            file.content_type
        )
        
        # Загружаем файл напрямую в MinIO через presigned URL
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.put(
                upload_url,
                content=content,
                headers={"Content-Type": file.content_type}
            )
            if response.status_code not in (200, 204):
                raise HTTPException(
                    status_code=500,
                    detail="Ошибка загрузки файла в хранилище"
                )
        
        # Создаём запись в БД
        image = LectureImage(
            lecture_id=lecture_id,
            filename=file.filename,
            storage_path=storage_path,
            mime_type=file.content_type,
            size_bytes=len(content)
        )
        db.add(image)
        await db.commit()
        await db.refresh(image)
        
        return image
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка загрузки изображения"
        )


@router.delete("/{lecture_id}/images/{image_id}")
async def delete_lecture_image(
    lecture_id: UUID,
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Удалить изображение лекции."""
    from sqlalchemy import select
    
    # Проверяем существование изображения
    result = await db.execute(
        select(LectureImage).where(
            LectureImage.id == image_id,
            LectureImage.lecture_id == lecture_id
        )
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Изображение не найдено")
    
    # Удаляем файл из MinIO
    try:
        await storage_service.delete_object(image.storage_path)
    except Exception as e:
        logger.warning(f"Failed to delete image from storage: {e}")
    
    # Удаляем из БД
    await db.delete(image)
    await db.commit()
    
    return {"status": "deleted"}
