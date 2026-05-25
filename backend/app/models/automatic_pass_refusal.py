from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .group_subject_offering import GroupSubjectOffering
    from .user import User


class AutomaticPassRefusal(Base, TimestampMixin):
    __tablename__ = "automatic_pass_refusals"
    __table_args__ = (UniqueConstraint("offering_id", "student_id", name="uq_automatic_pass_refusal_scope"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    offering_id: Mapped[UUID] = mapped_column(
        ForeignKey("group_subject_offerings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    declined_by_admin_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    offering: Mapped["GroupSubjectOffering"] = relationship()
    student: Mapped["User"] = relationship(foreign_keys=[student_id])
    declined_by_admin: Mapped["User | None"] = relationship(foreign_keys=[declined_by_admin_id])
