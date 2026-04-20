"""Admin endpoints for canonical group-subject offerings, exam prep, and automatic refusals."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.crud.crud_group_subject_offering import (
    clear_automatic_pass_refusal,
    get_current_semester_key,
    list_group_subject_offerings,
    upsert_automatic_pass_refusal,
)
from app.db.session import get_db
from app.models.group_subject_offering import FinalControlType, GroupSubjectOffering
from app.models.user import User, UserRole
from app.services.attestation.automatic_queue import list_offering_automatic_queue
from app.services.lab_settings_service import lab_settings_service

router = APIRouter()


class GroupSubjectOfferingResponse(BaseModel):
    id: UUID
    group_id: UUID
    group_name: str
    subject_id: UUID
    subject_name: str
    semester: str
    final_control_type: FinalControlType | None = None
    exam_prep_questions_count: int = 0


class GroupSubjectOfferingUpdate(BaseModel):
    final_control_type: FinalControlType | None = None


class AutomaticQueueStudentResponse(BaseModel):
    student_id: UUID
    student_name: str
    completed_count: int
    automatic_remaining: int
    completion_at: datetime | None = None
    queue_position: int | None = None
    is_winner: bool
    is_declined: bool
    declined_reason: str | None = None


class AutomaticQueueResponse(BaseModel):
    offering_id: UUID
    final_control_type: FinalControlType | None = None
    automatic_enabled: bool
    automatic_places: int | None = None
    total_labs: int
    students: list[AutomaticQueueStudentResponse]


class AutomaticPassRefusalUpdate(BaseModel):
    reason: str | None = None


class ExamPrepRichContent(BaseModel):
    text: str | None = None
    content: dict[str, Any] | None = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ExamPrepQuestionPayload(BaseModel):
    id: str = Field(min_length=1)
    prompt: str | ExamPrepRichContent
    answer: str | ExamPrepRichContent | None = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Question id is required")
        return normalized

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str | ExamPrepRichContent) -> str | ExamPrepRichContent:
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                raise ValueError("Question prompt is required")
            return normalized
        if not value.text and not value.content:
            raise ValueError("Question prompt is required")
        return value

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, value: str | ExamPrepRichContent | None) -> str | ExamPrepRichContent | None:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        if value is not None and not value.text and not value.content:
            return None
        return value


class ExamPrepPayload(BaseModel):
    questions: list[ExamPrepQuestionPayload] = Field(default_factory=list)


class AdminExamPrepResponse(BaseModel):
    offering_id: UUID
    questions_count: int
    questions: list[ExamPrepQuestionPayload]


def _serialize_offering(offering: GroupSubjectOffering) -> GroupSubjectOfferingResponse:
    return GroupSubjectOfferingResponse(
        id=offering.id,
        group_id=offering.group_id,
        group_name=offering.group.name if offering.group else "Unknown",
        subject_id=offering.subject_id,
        subject_name=offering.subject.name if offering.subject else "Unknown",
        semester=offering.semester,
        final_control_type=offering.final_control_type,
        exam_prep_questions_count=len(offering.exam_prep_questions or []),
    )


async def _get_offering_or_404(db: AsyncSession, offering_id: UUID) -> GroupSubjectOffering:
    result = await db.execute(
        select(GroupSubjectOffering)
        .options(selectinload(GroupSubjectOffering.group), selectinload(GroupSubjectOffering.subject))
        .where(GroupSubjectOffering.id == offering_id)
    )
    offering = result.scalar_one_or_none()
    if offering is None:
        raise HTTPException(status_code=404, detail="Связка предмета группы не найдена")
    return offering


async def _build_automatic_queue_response(db: AsyncSession, offering: GroupSubjectOffering) -> AutomaticQueueResponse:
    lab_settings = await lab_settings_service.get_lab_settings(db)
    automatic_enabled = bool(lab_settings and lab_settings.automatic_enabled)
    automatic_places = lab_settings.automatic_places if lab_settings else None
    total_labs = lab_settings.labs_count if lab_settings else 10
    students = await list_offering_automatic_queue(
        db,
        offering=offering,
        total_labs=total_labs,
        automatic_places=automatic_places,
    )
    return AutomaticQueueResponse(
        offering_id=offering.id,
        final_control_type=offering.final_control_type,
        automatic_enabled=automatic_enabled,
        automatic_places=automatic_places,
        total_labs=total_labs,
        students=[
            AutomaticQueueStudentResponse(
                student_id=entry.student_id,
                student_name=entry.student_name,
                completed_count=entry.completed_count,
                automatic_remaining=entry.automatic_remaining,
                completion_at=entry.completion_at,
                queue_position=entry.queue_position,
                is_winner=entry.is_winner,
                is_declined=entry.is_declined,
                declined_reason=entry.declined_reason,
            )
            for entry in students
        ],
    )


def _serialize_exam_prep(offering: GroupSubjectOffering) -> AdminExamPrepResponse:
    return AdminExamPrepResponse(
        offering_id=offering.id,
        questions_count=len(offering.exam_prep_questions or []),
        questions=[ExamPrepQuestionPayload.model_validate(question) for question in (offering.exam_prep_questions or [])],
    )


@router.get("/offerings", response_model=list[GroupSubjectOfferingResponse])
async def get_group_subject_offerings(
    semester: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
) -> list[GroupSubjectOfferingResponse]:
    resolved_semester = semester or await get_current_semester_key(db)
    offerings = await list_group_subject_offerings(db, semester=resolved_semester)
    return [_serialize_offering(offering) for offering in offerings]


@router.patch("/offerings/{offering_id}", response_model=GroupSubjectOfferingResponse)
async def update_group_subject_offering(
    offering_id: UUID,
    payload: GroupSubjectOfferingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> GroupSubjectOfferingResponse:
    offering = await _get_offering_or_404(db, offering_id)
    offering.final_control_type = payload.final_control_type
    await db.commit()
    return _serialize_offering(await _get_offering_or_404(db, offering_id))


@router.get("/offerings/{offering_id}/exam-prep", response_model=AdminExamPrepResponse)
async def get_offering_exam_prep(
    offering_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
) -> AdminExamPrepResponse:
    offering = await _get_offering_or_404(db, offering_id)
    return _serialize_exam_prep(offering)


@router.put("/offerings/{offering_id}/exam-prep", response_model=AdminExamPrepResponse)
async def update_offering_exam_prep(
    offering_id: UUID,
    payload: ExamPrepPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> AdminExamPrepResponse:
    offering = await _get_offering_or_404(db, offering_id)
    offering.exam_prep_questions = [question.model_dump(mode="json", exclude_none=True) for question in payload.questions]
    await db.commit()
    return _serialize_exam_prep(await _get_offering_or_404(db, offering_id))


@router.get("/offerings/{offering_id}/automatic-queue", response_model=AutomaticQueueResponse)
async def get_offering_automatic_queue(
    offering_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
) -> AutomaticQueueResponse:
    offering = await _get_offering_or_404(db, offering_id)
    return await _build_automatic_queue_response(db, offering)


@router.post("/offerings/{offering_id}/automatic-refusals/{student_id}", response_model=AutomaticQueueResponse)
async def decline_automatic_pass(
    offering_id: UUID,
    student_id: UUID,
    payload: AutomaticPassRefusalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> AutomaticQueueResponse:
    offering = await _get_offering_or_404(db, offering_id)
    student = await db.get(User, student_id)
    if student is None or student.group_id != offering.group_id or student.role != UserRole.STUDENT:
        raise HTTPException(status_code=404, detail="Студент не найден в группе выбранного предмета")

    await upsert_automatic_pass_refusal(
        db,
        offering_id=offering.id,
        student_id=student.id,
        declined_by_admin_id=current_user.id,
        reason=payload.reason,
    )
    await db.commit()
    return await _build_automatic_queue_response(db, offering)


@router.delete("/offerings/{offering_id}/automatic-refusals/{student_id}", response_model=AutomaticQueueResponse)
async def clear_declined_automatic_pass(
    offering_id: UUID,
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> AutomaticQueueResponse:
    offering = await _get_offering_or_404(db, offering_id)
    cleared = await clear_automatic_pass_refusal(
        db,
        offering_id=offering.id,
        student_id=student_id,
    )
    if not cleared:
        raise HTTPException(status_code=404, detail="Отказ от автомата не найден")
    await db.commit()
    return await _build_automatic_queue_response(db, offering)
