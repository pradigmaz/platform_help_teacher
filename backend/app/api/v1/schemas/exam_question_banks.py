from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.exam_question_bank import ExamQuestionBank
from app.models.group_subject_offering import GroupSubjectOffering
from app.services.exam_question_banks import get_exam_questions_count_for_offering


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


class OfferingRefResponse(BaseModel):
    offering_id: UUID
    group_id: UUID
    group_name: str
    subject_id: UUID
    subject_name: str
    semester: str
    questions_count: int


class ExamQuestionBankSummaryResponse(BaseModel):
    bank_id: UUID
    subject_id: UUID
    subject_name: str
    semester: str
    questions_count: int
    offerings: list[OfferingRefResponse]


class ExamQuestionBankDetailResponse(ExamQuestionBankSummaryResponse):
    questions: list[ExamPrepQuestionPayload]


class ExamSubjectGroupResponse(BaseModel):
    subject_id: UUID
    subject_name: str
    semester: str
    banks: list[ExamQuestionBankSummaryResponse]
    unassigned_offerings: list[OfferingRefResponse]


class ExamOfferingContextResponse(BaseModel):
    offering: OfferingRefResponse
    bank: ExamQuestionBankSummaryResponse | None = None
    compatible_banks: list[ExamQuestionBankSummaryResponse]


class CreateExamQuestionBankPayload(BaseModel):
    offering_ids: list[UUID] = Field(min_length=1)
    questions: list[ExamPrepQuestionPayload] = Field(default_factory=list)


class UpdateExamQuestionBankPayload(BaseModel):
    questions: list[ExamPrepQuestionPayload] = Field(default_factory=list)


class AssignExamQuestionBankPayload(BaseModel):
    offering_ids: list[UUID] = Field(min_length=1)


class SplitExamQuestionBankPayload(BaseModel):
    offering_ids: list[UUID] = Field(min_length=1)


def serialize_offering_ref(offering: GroupSubjectOffering) -> OfferingRefResponse:
    return OfferingRefResponse(
        offering_id=offering.id,
        group_id=offering.group_id,
        group_name=offering.group.name if offering.group else "Unknown",
        subject_id=offering.subject_id,
        subject_name=offering.subject.name if offering.subject else "Unknown",
        semester=offering.semester,
        questions_count=get_exam_questions_count_for_offering(offering),
    )


def serialize_bank_summary(bank: ExamQuestionBank) -> ExamQuestionBankSummaryResponse:
    offerings = sorted(bank.offerings, key=lambda offering: offering.group.name if offering.group else "")
    return ExamQuestionBankSummaryResponse(
        bank_id=bank.id,
        subject_id=bank.subject_id,
        subject_name=bank.subject.name if bank.subject else "Unknown",
        semester=bank.semester,
        questions_count=len(bank.questions),
        offerings=[serialize_offering_ref(offering) for offering in offerings],
    )


def serialize_bank_detail(bank: ExamQuestionBank) -> ExamQuestionBankDetailResponse:
    summary = serialize_bank_summary(bank)
    return ExamQuestionBankDetailResponse(
        **summary.model_dump(),
        questions=[ExamPrepQuestionPayload.model_validate(question) for question in bank.questions],
    )
