from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Any

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.lab import Lab
from app.models.submission import Submission
from app.schemas.lab import LabResponse

router = APIRouter()

@router.get("/", response_model=List[LabResponse])
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
        lab_dto.my_submission = subs_map.get(lab.id)
        response.append(lab_dto)
        
    return response