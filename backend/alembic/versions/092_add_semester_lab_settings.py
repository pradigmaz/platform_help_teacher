"""Add semester-specific global lab settings and automatic thresholds.

Revision ID: 092_add_semester_lab_settings
Revises: 091_normalize_attestation_bonus_activity
Create Date: 2026-04-16
"""

import sqlalchemy as sa

from alembic import op

revision = "092_add_semester_lab_settings"
down_revision = "091_normalize_attestation_bonus_activity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add semester-specific totals and automatic pass settings."""
    op.add_column(
        "lab_settings",
        sa.Column("labs_count_semester_1", sa.Integer(), nullable=True, server_default="10"),
    )
    op.add_column(
        "lab_settings",
        sa.Column("labs_count_semester_2", sa.Integer(), nullable=True, server_default="10"),
    )
    op.add_column("lab_settings", sa.Column("automatic_labs_semester_1", sa.Integer(), nullable=True))
    op.add_column("lab_settings", sa.Column("automatic_labs_semester_2", sa.Integer(), nullable=True))
    op.add_column("lab_settings", sa.Column("automatic_places", sa.Integer(), nullable=True))

    op.execute(
        """
        UPDATE lab_settings
        SET
            labs_count_semester_1 = COALESCE(labs_count, 10),
            labs_count_semester_2 = COALESCE(labs_count, 10)
        """
    )

    op.alter_column("lab_settings", "labs_count_semester_1", nullable=False, server_default=None)
    op.alter_column("lab_settings", "labs_count_semester_2", nullable=False, server_default=None)


def downgrade() -> None:
    """Remove semester-specific totals and automatic pass settings."""
    op.drop_column("lab_settings", "automatic_places")
    op.drop_column("lab_settings", "automatic_labs_semester_2")
    op.drop_column("lab_settings", "automatic_labs_semester_1")
    op.drop_column("lab_settings", "labs_count_semester_2")
    op.drop_column("lab_settings", "labs_count_semester_1")
