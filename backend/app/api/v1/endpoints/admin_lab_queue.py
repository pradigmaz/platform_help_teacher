"""
Admin Lab Queue API - очередь на сдачу лабораторных работ.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.core import error_messages as em
from app.db.session import get_db
from app.models import Lab, Lesson, Submission, SubmissionStatus, User
from app.models.schedule import LessonType
from app.services.attestation.deadline_validator import get_max_allowed_grade_for_lab
from app.services.schedule_constants import today_msk
from app.services.submission_service import submission_service

router = APIRouter()


# === Schemas ===


class QueueItemResponse(BaseModel):
    """Элемент очереди на сдачу."""

    submission_id: UUID
    student_id: UUID
    student_name: str
    group_name: str
    lab_id: UUID
    lab_number: int
    lab_title: str
    variant_number: int | None
    ready_at: datetime

    class Config:
        from_attributes = True


class LabQueueResponse(BaseModel):
    """Очередь по одной лабе."""

    lab_id: UUID
    lab_number: int
    lab_title: str
    queue: list[QueueItemResponse]


class AcceptSubmissionRequest(BaseModel):
    """Запрос на принятие работы."""

    grade: int = Field(..., ge=2, le=5, description="Оценка 2-5")
    comment: str | None = None


class RejectSubmissionRequest(BaseModel):
    """Запрос на отклонение работы."""

    comment: str = Field(..., min_length=1, description="Причина отклонения")


class SubmissionDetailResponse(BaseModel):
    """Детали сдачи для приёма работы."""

    submission_id: UUID
    student_id: UUID
    student_name: str
    group_id: UUID | None = None
    group_name: str
    lab_id: UUID
    lab_number: int
    lab_title: str
    variant_number: int | None = None
    variant_data: dict | None = None  # Данные варианта из lab.variants
    questions: list[Any] | None = None  # Контрольные вопросы (str или Lexical JSON dict)
    ready_at: datetime | None = None
    status: str
    max_allowed_grade: int = 5  # Максимальная оценка с учётом дедлайна (2-5)

    class Config:
        from_attributes = True


# === Endpoints ===


@router.get("/queue", response_model=list[LabQueueResponse])
async def get_submission_queue(
    subject_id: UUID | None = Query(default=None, description="Фильтр по предмету"),
    limit: int = Query(default=100, ge=1, le=500, description="Лимит записей в очереди"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> list[LabQueueResponse]:
    """
    Получить очередь на сдачу лабораторных работ.
    Группировка по лабам.
    """
    # Запрос сдач со статусом READY с фильтрацией в SQL
    query = (
        select(Submission)
        .where(Submission.status == SubmissionStatus.READY)
        .options(selectinload(Submission.user).selectinload(User.group), selectinload(Submission.lab))
        .order_by(Submission.ready_at.asc())
        .limit(limit)
    )

    # Фильтруем по предмету в SQL если указан
    if subject_id:
        query = query.join(Lab).where(Lab.subject_id == subject_id)

    result = await db.execute(query)
    submissions = result.scalars().all()

    # Группируем по лабам
    labs_dict: dict[UUID, LabQueueResponse] = {}

    for sub in submissions:
        lab = sub.lab
        student = sub.user
        group = student.group

        if lab.id not in labs_dict:
            labs_dict[lab.id] = LabQueueResponse(lab_id=lab.id, lab_number=lab.number, lab_title=lab.title, queue=[])

        labs_dict[lab.id].queue.append(
            QueueItemResponse(
                submission_id=sub.id,
                student_id=student.id,
                student_name=student.full_name or "Без имени",
                group_name=group.name if group else "Без группы",
                lab_id=lab.id,
                lab_number=lab.number,
                lab_title=lab.title,
                variant_number=sub.variant_number,
                ready_at=sub.ready_at,
            )
        )

    # Сортируем по номеру лабы
    return sorted(labs_dict.values(), key=lambda x: x.lab_number)


@router.get("/submissions/{submission_id}", response_model=SubmissionDetailResponse)
async def get_submission_detail(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> SubmissionDetailResponse:
    """Получить детали сдачи для приёма работы."""
    query = (
        select(Submission)
        .where(Submission.id == submission_id)
        .options(selectinload(Submission.user).selectinload(User.group), selectinload(Submission.lab))
    )

    result = await db.execute(query)
    sub = result.scalar_one_or_none()

    if not sub:
        raise HTTPException(status_code=404, detail=em.SUBMISSION_NOT_FOUND)

    lab = sub.lab
    student = sub.user
    group = student.group

    # Получаем данные варианта
    variant_data = None
    if sub.variant_number and lab.variants:
        for v in lab.variants:
            if v.get("number") == sub.variant_number:
                variant_data = v
                break

    # Вычисляем max_allowed_grade с учётом дедлайна
    max_allowed_grade = 5
    if lab.subject_id and student.group_id:
        lesson = await _find_lesson_for_grading(db, lab, student)
        if lesson:
            max_allowed_grade = await get_max_allowed_grade_for_lab(db, lab, lesson, student.id)

    return SubmissionDetailResponse(
        submission_id=sub.id,
        student_id=student.id,
        student_name=student.full_name or "Без имени",
        group_id=group.id if group else None,
        group_name=group.name if group else "Без группы",
        lab_id=lab.id,
        lab_number=lab.number,
        lab_title=lab.title or "Без названия",
        variant_number=sub.variant_number,
        variant_data=variant_data,
        questions=lab.questions if lab.questions else None,
        ready_at=sub.ready_at,
        status=sub.status.value if sub.status else "unknown",
        max_allowed_grade=max_allowed_grade,
    )


async def _find_lesson_for_grading(db: AsyncSession, lab: Lab, student: User) -> Lesson | None:
    """Найти занятие для определения дедлайна."""
    if not lab.subject_id or not student.group_id:
        return None

    today = today_msk()

    query = (
        select(Lesson)
        .where(
            Lesson.subject_id == lab.subject_id,
            Lesson.group_id == student.group_id,
            Lesson.lesson_type == LessonType.LAB,
            Lesson.date <= today,
            Lesson.is_cancelled.is_(False),
            or_(Lesson.subgroup == student.subgroup, Lesson.subgroup.is_(None)),
        )
        .order_by(Lesson.date.desc())
        .limit(1)
    )

    result = await db.execute(query)
    return result.scalar_one_or_none()


@router.post("/submissions/{submission_id}/accept")
async def accept_submission(
    submission_id: UUID,
    data: AcceptSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> dict[str, Any]:
    """
    Принять работу студента.
    Автоматически создаёт LessonGrade для синхронизации с журналом.
    """
    sub = await submission_service.get_by_id(db, submission_id, load_relations=True)
    if not sub:
        raise HTTPException(status_code=404, detail=em.SUBMISSION_NOT_FOUND)

    try:
        result = await submission_service.accept(db, sub, data.grade, data.comment, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/submissions/{submission_id}/reject")
async def reject_submission(
    submission_id: UUID,
    data: RejectSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> dict[str, Any]:
    """Отклонить работу студента."""
    sub = await submission_service.get_by_id(db, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail=em.SUBMISSION_NOT_FOUND)

    try:
        result = await submission_service.reject(db, sub, data.comment, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
