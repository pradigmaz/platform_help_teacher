"""Admin endpoints for shared exam question banks."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.api.v1.schemas.exam_question_banks import (
    AssignExamQuestionBankPayload,
    CreateExamQuestionBankPayload,
    ExamOfferingContextResponse,
    ExamQuestionBankDetailResponse,
    ExamSubjectGroupResponse,
    SplitExamQuestionBankPayload,
    UpdateExamQuestionBankPayload,
    serialize_bank_detail,
    serialize_bank_summary,
    serialize_offering_ref,
)
from app.crud.crud_group_subject_offering import get_current_semester_key, list_group_subject_offerings
from app.db.session import get_db
from app.models.exam_question_bank import ExamQuestionBank
from app.models.group_subject_offering import FinalControlType, GroupSubjectOffering
from app.models.user import User
from app.services.exam_question_banks import (
    get_exam_offering_or_404,
    get_exam_question_bank_or_404,
    get_exam_questions_count_for_offering,
    validate_bank_assignment,
    validate_bank_reassignment,
)

router = APIRouter()


async def _list_bank_groups(db: AsyncSession, *, semester: str) -> list[ExamSubjectGroupResponse]:
    offerings = await list_group_subject_offerings(db, semester=semester)
    exam_offerings = [offering for offering in offerings if offering.final_control_type == FinalControlType.EXAM]
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for offering in exam_offerings:
        key = (str(offering.subject_id), offering.semester)
        bucket = groups.setdefault(
            key,
            {
                "subject_id": offering.subject_id,
                "subject_name": offering.subject.name if offering.subject else "Unknown",
                "semester": offering.semester,
                "banks": {},
                "unassigned": [],
            },
        )
        if offering.exam_question_bank is None:
            bucket["unassigned"].append(offering)
            continue
        bucket["banks"][str(offering.exam_question_bank.id)] = offering.exam_question_bank

    result: list[ExamSubjectGroupResponse] = []
    for bucket in groups.values():
        banks = sorted(bucket["banks"].values(), key=lambda bank: str(bank.id))
        unassigned = sorted(bucket["unassigned"], key=lambda offering: offering.group.name if offering.group else "")
        result.append(
            ExamSubjectGroupResponse(
                subject_id=bucket["subject_id"],
                subject_name=bucket["subject_name"],
                semester=bucket["semester"],
                banks=[serialize_bank_summary(bank) for bank in banks],
                unassigned_offerings=[serialize_offering_ref(offering) for offering in unassigned],
            )
        )
    return sorted(result, key=lambda item: (item.subject_name, item.semester))


@router.get("/groups", response_model=list[ExamSubjectGroupResponse])
async def list_exam_question_bank_groups(
    semester: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> list[ExamSubjectGroupResponse]:
    return await _list_bank_groups(db, semester=semester or await get_current_semester_key(db))


@router.get("/banks/{bank_id}", response_model=ExamQuestionBankDetailResponse)
async def get_exam_question_bank(
    bank_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> ExamQuestionBankDetailResponse:
    return serialize_bank_detail(await get_exam_question_bank_or_404(db, bank_id))


@router.post("/banks", response_model=ExamQuestionBankDetailResponse)
async def create_exam_question_bank(
    payload: CreateExamQuestionBankPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> ExamQuestionBankDetailResponse:
    offerings = [await get_exam_offering_or_404(db, offering_id) for offering_id in payload.offering_ids]
    first = offerings[0]
    bank = ExamQuestionBank(
        subject_id=first.subject_id,
        semester=first.semester,
        questions=[question.model_dump(mode="json", exclude_none=True) for question in payload.questions],
    )
    db.add(bank)
    await db.flush()
    for offering in offerings:
        validate_bank_assignment(bank, offering)
        validate_bank_reassignment(offering)
        offering.exam_question_bank = bank
    await db.commit()
    return serialize_bank_detail(await get_exam_question_bank_or_404(db, bank.id))


@router.put("/banks/{bank_id}", response_model=ExamQuestionBankDetailResponse)
async def update_exam_question_bank(
    bank_id: UUID,
    payload: UpdateExamQuestionBankPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> ExamQuestionBankDetailResponse:
    bank = await get_exam_question_bank_or_404(db, bank_id)
    bank.questions = [question.model_dump(mode="json", exclude_none=True) for question in payload.questions]
    await db.commit()
    return serialize_bank_detail(await get_exam_question_bank_or_404(db, bank_id))


@router.post("/banks/{bank_id}/assign", response_model=ExamQuestionBankDetailResponse)
async def assign_exam_question_bank(
    bank_id: UUID,
    payload: AssignExamQuestionBankPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> ExamQuestionBankDetailResponse:
    bank = await get_exam_question_bank_or_404(db, bank_id)
    for offering_id in payload.offering_ids:
        offering = await get_exam_offering_or_404(db, offering_id)
        validate_bank_assignment(bank, offering)
        validate_bank_reassignment(offering, target_bank_id=bank.id)
        offering.exam_question_bank = bank
    await db.commit()
    return serialize_bank_detail(await get_exam_question_bank_or_404(db, bank_id))


@router.post("/banks/{bank_id}/split", response_model=ExamQuestionBankDetailResponse)
async def split_exam_question_bank(
    bank_id: UUID,
    payload: SplitExamQuestionBankPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> ExamQuestionBankDetailResponse:
    source_bank = await get_exam_question_bank_or_404(db, bank_id)
    if len(source_bank.offerings) <= 1:
        raise HTTPException(status_code=400, detail="Нельзя разделить банк, к которому привязана только одна группа")
    selected_offering_ids = set(payload.offering_ids)
    if len(selected_offering_ids) >= len(source_bank.offerings):
        raise HTTPException(status_code=400, detail="Нельзя перенести все группы в новый банк")

    next_bank = ExamQuestionBank(
        subject_id=source_bank.subject_id,
        semester=source_bank.semester,
        questions=list(source_bank.questions),
    )
    db.add(next_bank)
    await db.flush()
    for offering_id in selected_offering_ids:
        offering = await get_exam_offering_or_404(db, offering_id)
        if offering.exam_question_bank_id != source_bank.id:
            raise HTTPException(status_code=400, detail="Можно разделить только уже привязанные к банку группы")
        offering.exam_question_bank = next_bank
    await db.commit()
    return serialize_bank_detail(await get_exam_question_bank_or_404(db, next_bank.id))


@router.get("/offerings/{offering_id}/context", response_model=ExamOfferingContextResponse)
async def get_exam_offering_context(
    offering_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> ExamOfferingContextResponse:
    offering = await get_exam_offering_or_404(db, offering_id)
    if offering.final_control_type != FinalControlType.EXAM:
        raise HTTPException(status_code=400, detail="Контекст вопросов доступен только для экзаменационной связки")

    result = await db.execute(
        select(ExamQuestionBank)
        .options(
            selectinload(ExamQuestionBank.subject),
            selectinload(ExamQuestionBank.offerings).selectinload(GroupSubjectOffering.group),
            selectinload(ExamQuestionBank.offerings).selectinload(GroupSubjectOffering.subject),
        )
        .where(
            ExamQuestionBank.subject_id == offering.subject_id,
            ExamQuestionBank.semester == offering.semester,
        )
        .order_by(ExamQuestionBank.id.asc())
    )
    compatible_banks = list(result.scalars().all())
    assigned_bank = next((bank for bank in compatible_banks if bank.id == offering.exam_question_bank_id), None)
    remaining_banks = [bank for bank in compatible_banks if bank.id != offering.exam_question_bank_id]
    return ExamOfferingContextResponse(
        offering=serialize_offering_ref(offering),
        bank=serialize_bank_summary(assigned_bank) if assigned_bank else None,
        compatible_banks=[serialize_bank_summary(bank) for bank in remaining_banks],
    )
