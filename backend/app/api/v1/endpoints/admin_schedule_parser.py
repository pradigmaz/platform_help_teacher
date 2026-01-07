"""
API для автопарсера расписания
"""
import logging
from datetime import date, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_teacher
from app.models.user import User
from app.schemas.schedule_parser import (
    ParserConfigCreate,
    ParserConfigUpdate,
    ParserConfigResponse,
    ScheduleConflictResponse,
    ConflictResolveRequest,
    ParseHistoryResponse
)
from app.crud import crud_schedule_parser as crud
from app.crud import crud_parse_history
from app.services.schedule_import_service import ScheduleImportService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/parser-config", response_model=ParserConfigResponse | None)
async def get_parser_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получить настройки автопарсера"""
    config = await crud.get_parser_config(db, current_user.id)
    return config


@router.post("/parser-config", response_model=ParserConfigResponse)
async def create_or_update_parser_config(
    data: ParserConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Создать или обновить настройки автопарсера"""
    existing = await crud.get_parser_config(db, current_user.id)
    
    if existing:
        update_data = ParserConfigUpdate(**data.model_dump())
        return await crud.update_parser_config(db, existing, update_data)
    else:
        return await crud.create_parser_config(db, current_user.id, data)


@router.get("/conflicts", response_model=list[ScheduleConflictResponse])
async def get_conflicts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получить неразрешённые конфликты"""
    conflicts = await crud.get_unresolved_conflicts(db, current_user.id)
    return conflicts


@router.post("/conflicts/{conflict_id}/resolve", response_model=ScheduleConflictResponse)
async def resolve_conflict(
    conflict_id: UUID,
    data: ConflictResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Разрешить конфликт"""
    conflict = await crud.resolve_conflict(db, conflict_id, data.action)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    return conflict


@router.post("/conflicts/resolve-all")
async def resolve_all_conflicts(
    data: ConflictResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Разрешить все конфликты текущего преподавателя"""
    count = await crud.resolve_all_conflicts(db, data.action, current_user.id)
    return {"resolved": count}


@router.post("/parse-now")
async def parse_now(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Запустить парсинг вручную"""
    config = await crud.get_parser_config(db, current_user.id)
    if not config:
        raise HTTPException(status_code=400, detail="Parser config not found")
    
    service = ScheduleImportService(db)
    start_date = date.today()
    end_date = start_date + timedelta(days=config.parse_days_ahead)
    
    try:
        stats = await service.import_from_parser(
            teacher_name=config.teacher_name,
            start_date=start_date,
            end_date=end_date
        )
        return stats
    except Exception as e:
        logger.exception("Parse error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parse-history", response_model=list[ParseHistoryResponse])
async def get_parse_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получить историю парсинга"""
    history = await crud_parse_history.get_history(db, current_user.id, limit)
    return history
