from sqlalchemy import Text, Float, ForeignKey, Boolean, Enum as SAEnum, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4
from typing import Optional, TYPE_CHECKING
from app.models.base import Base, TimestampMixin
from app.models.attestation_settings import AttestationType

if TYPE_CHECKING:
    from app.models.user import User

class Activity(Base, TimestampMixin):
    __tablename__ = "activities"
    __table_args__ = (
        CheckConstraint("length(description) <= 500", name="ck_activities_description_len"),
        Index("ix_activities_created_at", "created_at"),
        Index("ix_activities_attestation_type", "attestation_type"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    points: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Тип аттестации (first/second), к которому относится активность
    attestation_type: Mapped[AttestationType] = mapped_column(
        SAEnum(AttestationType, name='attestationtype', create_constraint=False, native_enum=False),
        nullable=False
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    batch_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True) # Для группировки массовых начислений
    
    created_by_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id], backref="activities")
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])

