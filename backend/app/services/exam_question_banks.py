from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.exam_question_bank import ExamQuestionBank
from app.models.group_subject_offering import FinalControlType, GroupSubjectOffering


def get_exam_questions_for_offering(offering: GroupSubjectOffering) -> list[dict]:
    if offering.exam_question_bank is not None:
        return offering.exam_question_bank.questions
    return offering.exam_prep_questions or []


def get_exam_questions_count_for_offering(offering: GroupSubjectOffering) -> int:
    return len(get_exam_questions_for_offering(offering))


async def get_exam_question_bank_or_404(db: AsyncSession, bank_id: UUID) -> ExamQuestionBank:
    result = await db.execute(
        select(ExamQuestionBank)
        .options(
            selectinload(ExamQuestionBank.subject),
            selectinload(ExamQuestionBank.offerings).selectinload(GroupSubjectOffering.group),
            selectinload(ExamQuestionBank.offerings).selectinload(GroupSubjectOffering.subject),
        )
        .where(ExamQuestionBank.id == bank_id)
    )
    bank = result.scalar_one_or_none()
    if bank is None:
        raise HTTPException(status_code=404, detail="Банк экзаменационных вопросов не найден")
    return bank


async def get_exam_offering_or_404(db: AsyncSession, offering_id: UUID) -> GroupSubjectOffering:
    result = await db.execute(
        select(GroupSubjectOffering)
        .options(
            selectinload(GroupSubjectOffering.group),
            selectinload(GroupSubjectOffering.subject),
            selectinload(GroupSubjectOffering.exam_question_bank),
        )
        .where(GroupSubjectOffering.id == offering_id)
    )
    offering = result.scalar_one_or_none()
    if offering is None:
        raise HTTPException(status_code=404, detail="Связка предмета группы не найдена")
    return offering


async def list_exam_offerings_for_subject_semester(
    db: AsyncSession,
    *,
    subject_id: UUID,
    semester: str,
) -> list[GroupSubjectOffering]:
    result = await db.execute(
        select(GroupSubjectOffering)
        .options(
            selectinload(GroupSubjectOffering.group),
            selectinload(GroupSubjectOffering.subject),
            selectinload(GroupSubjectOffering.exam_question_bank),
        )
        .where(
            GroupSubjectOffering.subject_id == subject_id,
            GroupSubjectOffering.semester == semester,
            GroupSubjectOffering.final_control_type == FinalControlType.EXAM,
        )
        .order_by(GroupSubjectOffering.group_id.asc(), GroupSubjectOffering.id.asc())
    )
    return list(result.scalars().all())


def validate_bank_assignment(bank: ExamQuestionBank, offering: GroupSubjectOffering) -> None:
    if offering.final_control_type != FinalControlType.EXAM:
        raise HTTPException(status_code=400, detail="Привязать банк можно только к экзаменационной связке")
    if bank.subject_id != offering.subject_id or bank.semester != offering.semester:
        raise HTTPException(status_code=400, detail="Банк можно привязать только к тому же предмету и семестру")


def validate_bank_reassignment(offering: GroupSubjectOffering, *, target_bank_id: UUID | None = None) -> None:
    current_bank_id = offering.exam_question_bank_id
    if current_bank_id is None:
        return
    if target_bank_id is not None and current_bank_id == target_bank_id:
        return
    raise HTTPException(
        status_code=400,
        detail="Группа уже привязана к другому банку. Сначала разделите текущую привязку или выберите группу без банка.",
    )
