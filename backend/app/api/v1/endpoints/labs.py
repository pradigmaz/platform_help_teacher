from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.audit import ActionType, EntityType, audit_action
from app.core.limiter import limiter
from app.models.lab import Lab
from app.models.submission import Submission
from app.models.user import User
from app.schemas.lab import LabResponse, SubmissionDTO
from app.services.lab_service import lab_service

router = APIRouter()


@router.get("/view/{code}", response_model=LabResponse)
@limiter.limit("30/minute")
@audit_action(ActionType.VIEW, EntityType.LAB)
async def get_public_lab(
    request: Request,
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """Получить лабораторную по публичному коду (без авторизации)."""
    lab = await lab_service.get_by_public_code(db, code)
    if not lab:
        raise HTTPException(status_code=404, detail="Лабораторная не найдена")

    return lab


@router.get("/", response_model=list[LabResponse])
async def get_labs_with_status(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Получить список всех лаб с приклеенным статусом сдачи текущего студента.
    """
    # 1. Забираем все лабы
    result = await db.execute(select(Lab).order_by(Lab.created_at.desc()).offset(skip).limit(limit))
    labs = result.scalars().all()

    # 2. Забираем все сдачи этого студента
    stmt_subs = select(Submission).where(Submission.user_id == current_user.id)
    result_subs = await db.execute(stmt_subs)
    submissions = result_subs.scalars().all()

    # 3. Мапим submissions по lab_id для быстрого поиска
    subs_map = {sub.lab_id: sub for sub in submissions}

    # 4. Собираем ответ
    response = []
    for lab in labs:
        lab_dto = LabResponse.model_validate(lab)
        submission = subs_map.get(lab.id)
        lab_dto.my_submission = SubmissionDTO.model_validate(submission) if submission is not None else None
        response.append(lab_dto)

    return response
