"""Offering-scoped academic threshold policy."""

from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class GroupSubjectOfferingPolicy(Base, TimestampMixin):
    """Mutable lab/attestation/automatic thresholds for one offering."""

    __tablename__ = "group_subject_offering_policies"
    __table_args__ = (
        CheckConstraint("total_labs >= 0", name="ck_offering_policy_total_labs_nonnegative"),
        CheckConstraint("labs_required_first >= 0", name="ck_offering_policy_first_nonnegative"),
        CheckConstraint(
            "labs_required_second_total >= labs_required_first", name="ck_offering_policy_second_after_first"
        ),
        CheckConstraint("labs_required_second_total <= total_labs", name="ck_offering_policy_second_within_total"),
        CheckConstraint("exam_admission_required_labs >= 0", name="ck_offering_policy_exam_nonnegative"),
        CheckConstraint("exam_admission_required_labs <= total_labs", name="ck_offering_policy_exam_within_total"),
        CheckConstraint(
            "automatic_places IS NULL OR automatic_places >= 0", name="ck_offering_policy_places_nonnegative"
        ),
        CheckConstraint("automatic_required_labs_total >= 0", name="ck_offering_policy_auto_nonnegative"),
        CheckConstraint("automatic_required_labs_total <= total_labs", name="ck_offering_policy_auto_within_total"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    offering_id: Mapped[UUID] = mapped_column(
        ForeignKey("group_subject_offerings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    total_labs: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    labs_required_first: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    labs_required_second_total: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    exam_admission_required_labs: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    automatic_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    automatic_places: Mapped[int | None] = mapped_column(Integer, nullable=True)
    automatic_required_labs_total: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    offering = relationship("GroupSubjectOffering")
