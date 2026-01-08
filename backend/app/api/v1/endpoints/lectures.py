"""Публичные API endpoints для лекций (без авторизации)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.crud.crud_lecture import crud_lecture
from app.schemas.lecture import LectureResponse
from app.core.limiter import limiter
from app.audit import audit_action, ActionType, EntityType

router = APIRouter()


@router.get("/view/{code}", response_model=LectureResponse)
@limiter.limit("30/minute")
@audit_action(ActionType.VIEW, EntityType.LECTURE)
async def get_public_lecture(
    request: Request,
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """Получить лекцию по публичному коду (без авторизации)."""
    lecture = await crud_lecture.get_by_public_code(db, code)
    if not lecture:
        raise HTTPException(status_code=404, detail="Лекция не найдена")
    
    if not lecture.is_published:
        raise HTTPException(status_code=404, detail="Лекция не найдена")
    
    return lecture
