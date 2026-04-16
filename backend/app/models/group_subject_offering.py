from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .group import Group
    from .subject import Subject


class FinalControlType(str, Enum):
    EXAM = "exam"
    CREDIT = "credit"
    DIFFERENTIATED_CREDIT = "differentiated_credit"


class GroupSubjectOffering(Base, TimestampMixin):
    __tablename__ = "group_subject_offerings"
    __table_args__ = (
        UniqueConstraint("group_id", "subject_id", "semester", name="uq_group_subject_offering_scope"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    group_id: Mapped[UUID] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    semester: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    final_control_type: Mapped[FinalControlType | None] = mapped_column(
        SQLEnum(FinalControlType, name="finalcontroltype", create_constraint=False, native_enum=False),
        nullable=True,
        default=None,
    )

    group: Mapped["Group"] = relationship()
    subject: Mapped["Subject"] = relationship()
