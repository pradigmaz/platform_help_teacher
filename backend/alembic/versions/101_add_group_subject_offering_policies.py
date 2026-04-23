"""Add offering-scoped academic policy table.

Revision ID: 101_add_group_subject_offering_policies
Revises: 100_add_exam_question_banks
Create Date: 2026-04-23
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "101_add_group_subject_offering_policies"
down_revision = "100_add_exam_question_banks"
branch_labels = None
depends_on = None

policy_table = sa.table(
    "group_subject_offering_policies",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("offering_id", postgresql.UUID(as_uuid=True)),
    sa.column("total_labs", sa.Integer()),
    sa.column("labs_required_first", sa.Integer()),
    sa.column("labs_required_second_total", sa.Integer()),
    sa.column("exam_admission_required_labs", sa.Integer()),
    sa.column("automatic_enabled", sa.Boolean()),
    sa.column("automatic_places", sa.Integer()),
    sa.column("automatic_required_labs_total", sa.Integer()),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)
offering_table = sa.table(
    "group_subject_offerings",
    sa.column("id", postgresql.UUID(as_uuid=True)),
)
lab_settings_table = sa.table(
    "lab_settings",
    sa.column("labs_count", sa.Integer()),
    sa.column("automatic_enabled", sa.Boolean()),
    sa.column("automatic_places", sa.Integer()),
)
attestation_settings_table = sa.table(
    "attestation_settings",
    sa.column("attestation_type", sa.String()),
    sa.column("labs_count_first", sa.Integer()),
    sa.column("labs_count_second", sa.Integer()),
)


def upgrade() -> None:
    op.create_table(
        "group_subject_offering_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("offering_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_labs", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("labs_required_first", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("labs_required_second_total", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("exam_admission_required_labs", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("automatic_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("automatic_places", sa.Integer(), nullable=True),
        sa.Column("automatic_required_labs_total", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("total_labs >= 0", name="ck_offering_policy_total_labs_nonnegative"),
        sa.CheckConstraint("labs_required_first >= 0", name="ck_offering_policy_first_nonnegative"),
        sa.CheckConstraint("labs_required_second_total >= labs_required_first", name="ck_offering_policy_second_after_first"),
        sa.CheckConstraint("labs_required_second_total <= total_labs", name="ck_offering_policy_second_within_total"),
        sa.CheckConstraint("exam_admission_required_labs >= 0", name="ck_offering_policy_exam_nonnegative"),
        sa.CheckConstraint("exam_admission_required_labs <= total_labs", name="ck_offering_policy_exam_within_total"),
        sa.CheckConstraint("automatic_places IS NULL OR automatic_places >= 0", name="ck_offering_policy_places_nonnegative"),
        sa.CheckConstraint("automatic_required_labs_total >= 0", name="ck_offering_policy_auto_nonnegative"),
        sa.CheckConstraint("automatic_required_labs_total <= total_labs", name="ck_offering_policy_auto_within_total"),
        sa.ForeignKeyConstraint(["offering_id"], ["group_subject_offerings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("offering_id", name="uq_group_subject_offering_policy_offering"),
    )
    op.create_index(
        op.f("ix_group_subject_offering_policies_offering_id"),
        "group_subject_offering_policies",
        ["offering_id"],
        unique=True,
    )

    connection = op.get_bind()
    lab_row = connection.execute(sa.select(lab_settings_table).limit(1)).mappings().first()
    first_row = connection.execute(
        sa.select(attestation_settings_table).where(attestation_settings_table.c.attestation_type == "FIRST")
    ).mappings().first()
    second_row = connection.execute(
        sa.select(attestation_settings_table).where(attestation_settings_table.c.attestation_type == "SECOND")
    ).mappings().first()

    total_labs = int(lab_row["labs_count"]) if lab_row and lab_row["labs_count"] is not None else 10
    labs_required_first = int(first_row["labs_count_first"]) if first_row else min(8, total_labs)
    second_extra = int(second_row["labs_count_second"]) if second_row else max(total_labs - labs_required_first, 0)
    labs_required_second_total = labs_required_first + second_extra
    automatic_enabled = bool(lab_row["automatic_enabled"]) if lab_row else True
    automatic_places = lab_row["automatic_places"] if lab_row else None
    now = datetime.now(timezone.utc)

    rows = connection.execute(sa.select(offering_table.c.id)).mappings()
    for row in rows:
        exists = connection.execute(
            sa.select(policy_table.c.offering_id).where(policy_table.c.offering_id == row["id"])
        ).first()
        if exists:
            continue
        connection.execute(
            sa.insert(policy_table).values(
                id=uuid4(),
                offering_id=row["id"],
                total_labs=total_labs,
                labs_required_first=labs_required_first,
                labs_required_second_total=labs_required_second_total,
                exam_admission_required_labs=labs_required_second_total,
                automatic_enabled=automatic_enabled,
                automatic_places=automatic_places,
                automatic_required_labs_total=total_labs,
                created_at=now,
                updated_at=now,
            )
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_group_subject_offering_policies_offering_id"), table_name="group_subject_offering_policies")
    op.drop_table("group_subject_offering_policies")
