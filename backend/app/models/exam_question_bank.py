from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .group_subject_offering import GroupSubjectOffering
    from .subject import Subject


class ExamQuestionBank(Base, TimestampMixin):
    __tablename__ = "exam_question_banks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    subject_id: Mapped[UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    semester: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)

    subject: Mapped["Subject"] = relationship()
    offerings: Mapped[list["GroupSubjectOffering"]] = relationship(back_populates="exam_question_bank")
