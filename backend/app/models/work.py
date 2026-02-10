from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .work_type import WorkType

if TYPE_CHECKING:
    from .group import Group
    from .subject import Subject
    from .work_submission import WorkSubmission


class Work(Base, TimestampMixin):
    """Универсальная модель работы (контрольные, самостоятельные, коллоквиумы, проекты)"""
    __tablename__ = "works"
    __table_args__ = (
        CheckConstraint("length(title) <= 200", name="ck_works_title_len"),
        CheckConstraint("length(s3_key) <= 500", name="ck_works_s3_key_len"),
        CheckConstraint("max_grade > 0 AND max_grade <= 100", name="ck_works_max_grade"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_type: Mapped[WorkType] = mapped_column(
        SAEnum(WorkType, name='worktype', create_constraint=False, native_enum=True, create_type=False),
        nullable=False,
        index=True
    )
    max_grade: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)  # Файл задания

    # Привязка к предмету и группе
    subject_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True
    )
    group_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="SET NULL"),
        nullable=True
    )

    # Связи
    submissions: Mapped[list["WorkSubmission"]] = relationship(
        back_populates="work", cascade="all, delete-orphan"
    )
    subject: Mapped[Optional["Subject"]] = relationship()
    group: Mapped[Optional["Group"]] = relationship()
