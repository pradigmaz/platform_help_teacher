"""API эндпоинты для управления сдачей работ."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api import deps
from app.db.session import get_db
from app.models import User
from app.models.work_type import WorkType
from app.crud.crud_work import work as crud_work
from app.crud.crud_work_submission import work_submission as crud_submission

router = APIRouter()


class WorkSubmissionCreate(BaseModel):
    work_id: UUID
    user_id: UUID
    grade: Optional[int] = Field(None, ge=0, le=100)
    feedback: Optional[str] = None
    s3_key: Optional[str] = None
    is_manual: bool = False


class WorkSubmissionUpdateGrade(BaseModel):
    grade: int = Field(..., ge=0, le=100)
    feedback: Optional[str] = None


class WorkSubmissionResponse(BaseModel):
    id: UUID
    work_id: UUID
    user_id: UUID
    grade: Optional[int]
    feedback: Optional[str]
    s3_key: Optional[str]
    is_manual: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/work-submissions", response_model=WorkSubmissionResponse)
async def create_submission(
    submission_in: WorkSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Создать сдачу работы (выставить оценку)."""
    # Проверяем существование работы
    work_obj = await crud_work.get(db, submission_in.work_id)
    if not work_obj:
        raise HTTPException(status_code=404, detail="Работа не найдена")
    
    # Проверяем, нет ли уже сдачи
    existing = await crud_submission.get_by_student_and_work(
        db, submission_in.user_id, submission_in.work_id
    )
    if existing:
        raise HTTPException(status_code=400, detail="Сдача уже существует, используйте PATCH для обновления")
    
    submission = await crud_submission.create(
        db,
        work_id=submission_in.work_id,
        user_id=submission_in.user_id,
        grade=submission_in.grade,
        feedback=submission_in.feedback,
        s3_key=submission_in.s3_key,
        is_manual=submission_in.is_manual
    )
    return submission


@router.get("/work-submissions/student/{user_id}", response_model=List[WorkSubmissionResponse])
async def get_student_submissions(
    user_id: UUID,
    work_type: Optional[WorkType] = Query(None, description="Фильтр по типу работы"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить сдачи студента."""
    submissions = await crud_submission.get_by_student(db, user_id, work_type)
    return submissions


@router.get("/work-submissions/work/{work_id}", response_model=List[WorkSubmissionResponse])
async def get_work_submissions(
    work_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить все сдачи для работы."""
    submissions = await crud_submission.get_by_work(db, work_id)
    return submissions


@router.patch("/work-submissions/{submission_id}/grade", response_model=WorkSubmissionResponse)
async def update_submission_grade(
    submission_id: UUID,
    grade_in: WorkSubmissionUpdateGrade,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить оценку за работу."""
    submission = await crud_submission.get(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Сдача не найдена")
    
    submission = await crud_submission.update_grade(
        db,
        db_obj=submission,
        grade=grade_in.grade,
        feedback=grade_in.feedback
    )
    return submission


@router.delete("/work-submissions/{submission_id}")
async def delete_submission(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Удалить сдачу работы."""
    deleted = await crud_submission.delete(db, id=submission_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Сдача не найдена")
    return {"status": "deleted"}
