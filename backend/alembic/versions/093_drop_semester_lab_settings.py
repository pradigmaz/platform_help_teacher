"""Drop semester-specific lab settings fields.

Revision ID: 093_drop_semester_lab_settings
Revises: 092_add_semester_lab_settings
Create Date: 2026-04-16
"""

import sqlalchemy as sa

from alembic import op

revision = "093_drop_semester_lab_settings"
down_revision = "092_add_semester_lab_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove semester-specific lab settings fields."""
    op.drop_column("lab_settings", "automatic_labs_semester_2")
    op.drop_column("lab_settings", "automatic_labs_semester_1")
    op.drop_column("lab_settings", "labs_count_semester_2")
    op.drop_column("lab_settings", "labs_count_semester_1")


def downgrade() -> None:
    """Restore semester-specific lab settings fields from the shared total."""
    op.add_column("lab_settings", sa.Column("labs_count_semester_1", sa.Integer(), nullable=True))
    op.add_column("lab_settings", sa.Column("labs_count_semester_2", sa.Integer(), nullable=True))
    op.add_column("lab_settings", sa.Column("automatic_labs_semester_1", sa.Integer(), nullable=True))
    op.add_column("lab_settings", sa.Column("automatic_labs_semester_2", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE lab_settings
        SET
            labs_count_semester_1 = COALESCE(labs_count, 10),
            labs_count_semester_2 = COALESCE(labs_count, 10)
        """
    )
    op.alter_column("lab_settings", "labs_count_semester_1", nullable=False)
    op.alter_column("lab_settings", "labs_count_semester_2", nullable=False)
