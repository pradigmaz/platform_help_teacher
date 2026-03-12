"""Add partial unique constraint on labs(subject_id, number) where deleted_at IS NULL

Revision ID: 083_labs_subject_number_uq
Revises: 082_fix_device_datetime_tz
Create Date: 2026-03-06
"""

from alembic import op

revision = "083_labs_subject_number_uq"
down_revision = "082_fix_device_datetime_tz"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Partial unique index: только среди не удалённых лаб
    op.execute(
        """
        CREATE UNIQUE INDEX uq_labs_subject_number
        ON labs (subject_id, number)
        WHERE deleted_at IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_labs_subject_number")
