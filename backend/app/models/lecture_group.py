from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4

from .base import Base, TimestampMixin

class LectureGroup(Base, TimestampMixin):
    __tablename__ = "lecture_groups"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lecture_id: Mapped[UUID] = mapped_column(ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False)
    group_id: Mapped[UUID] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint('lecture_id', 'group_id', name='uq_lecture_group'),
    )