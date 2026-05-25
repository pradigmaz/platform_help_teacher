from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .exam_question_bank import ExamQuestionBank
    from .group import Group
    from .subject import Subject


class FinalControlType(str, Enum):
    EXAM = "exam"
    CREDIT = "credit"
    DIFFERENTIATED_CREDIT = "differentiated_credit"


class GroupSubjectOffering(Base, TimestampMixin):
    __tablename__ = "group_subject_offerings"
    __table_args__ = (UniqueConstraint("group_id", "subject_id", "semester", name="uq_group_subject_offering_scope"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    group_id: Mapped[UUID] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    semester: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    final_control_type: Mapped[FinalControlType | None] = mapped_column(
        SQLEnum(FinalControlType, name="finalcontroltype", create_constraint=False, native_enum=False),
        nullable=True,
        default=None,
    )
    exam_question_bank_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("exam_question_banks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    exam_prep_questions: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
    )

    group: Mapped["Group"] = relationship()
    subject: Mapped["Subject"] = relationship()
    exam_question_bank: Mapped["ExamQuestionBank | None"] = relationship(back_populates="offerings")
