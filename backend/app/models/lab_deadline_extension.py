"""
Модель продления дедлайна лабораторной для группы.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.lab import Lab
    from app.models.user import User


class LabDeadlineExtension(Base, TimestampMixin):
    """
    Временное продление дедлайна лабораторной для конкретной группы.

    Позволяет дать группе дополнительные пары для сдачи на максимальный балл.
    """
    __tablename__ = "lab_deadline_extensions"
    __table_args__ = (
        UniqueConstraint('lab_id', 'group_id', name='uq_lab_deadline_extension_lab_group'),
        Index('ix_lab_deadline_extensions_lab_id', 'lab_id'),
        Index('ix_lab_deadline_extensions_group_id', 'group_id'),
        Index('ix_lab_deadline_extensions_is_active', 'is_active'),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Для какой лабы
    lab_id: Mapped[UUID] = mapped_column(
        ForeignKey("labs.id", ondelete="CASCADE"),
        nullable=False
    )

    # Для какой группы
    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False
    )

    # Сколько дополнительных пар даётся
    bonus_lessons: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Причина продления
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Когда продление истекает (если None — бессрочно, пока не деактивируют)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Активно ли продление
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Кто создал
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    lab: Mapped["Lab"] = relationship("Lab", back_populates="deadline_extensions")
    group: Mapped["Group"] = relationship("Group")
    creator: Mapped[Optional["User"]] = relationship("User")
