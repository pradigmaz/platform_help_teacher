"""Student exam prep endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.crud.crud_group_subject_offering import get_current_semester_key, list_group_subject_offerings_for_group
from app.models.group_subject_offering import FinalControlType, GroupSubjectOffering
from app.models.user import User

router = APIRouter()


class StudentExamPrepQuestion(BaseModel):
    id: str
    prompt: str | dict[str, Any]
    answer: str | dict[str, Any] | None = None


class StudentExamPrepOffering(BaseModel):
    offering_id: UUID
    subject_id: UUID
    subject_name: str
    semester: str
    questions_count: int


class StudentExamPrepResponse(BaseModel):
    offering_id: UUID
    subject_id: UUID
    subject_name: str
    semester: str
    questions_count: int
    questions: list[StudentExamPrepQuestion]


def _serialize_exam_offering(offering: GroupSubjectOffering) -> StudentExamPrepOffering:
    return StudentExamPrepOffering(
        offering_id=offering.id,
        subject_id=offering.subject_id,
        subject_name=offering.subject.name if offering.subject else "Unknown",
        semester=offering.semester,
        questions_count=len(offering.exam_prep_questions or []),
    )


async def _get_student_exam_offering_or_404(
    db: AsyncSession,
    *,
    current_user: User,
    offering_id: UUID,
) -> GroupSubjectOffering:
    if current_user.group_id is None:
        raise HTTPException(status_code=404, detail="Экзамен не найден")

    semester = await get_current_semester_key(db)
    result = await db.execute(
        select(GroupSubjectOffering)
        .options(selectinload(GroupSubjectOffering.subject))
        .where(
            GroupSubjectOffering.id == offering_id,
            GroupSubjectOffering.group_id == current_user.group_id,
            GroupSubjectOffering.semester == semester,
            GroupSubjectOffering.final_control_type == FinalControlType.EXAM,
        )
    )
    offering = result.scalar_one_or_none()
    if offering is None:
        raise HTTPException(status_code=404, detail="Экзамен не найден")
    return offering


@router.get("/exam-prep/offerings", response_model=list[StudentExamPrepOffering])
async def list_student_exam_prep_offerings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[StudentExamPrepOffering]:
    if current_user.group_id is None:
        return []

    semester = await get_current_semester_key(db)
    offerings = await list_group_subject_offerings_for_group(
        db,
        group_id=current_user.group_id,
        semester=semester,
    )
    exam_offerings = [offering for offering in offerings if offering.final_control_type == FinalControlType.EXAM]
    exam_offerings.sort(key=lambda offering: (offering.subject.name if offering.subject else "", str(offering.id)))
    return [_serialize_exam_offering(offering) for offering in exam_offerings]


@router.get("/exam-prep/{offering_id}", response_model=StudentExamPrepResponse)
async def get_student_exam_prep(
    offering_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentExamPrepResponse:
    offering = await _get_student_exam_offering_or_404(
        db,
        current_user=current_user,
        offering_id=offering_id,
    )
    return StudentExamPrepResponse(
        offering_id=offering.id,
        subject_id=offering.subject_id,
        subject_name=offering.subject.name if offering.subject else "Unknown",
        semester=offering.semester,
        questions_count=len(offering.exam_prep_questions or []),
        questions=[StudentExamPrepQuestion.model_validate(question) for question in (offering.exam_prep_questions or [])],
    )
