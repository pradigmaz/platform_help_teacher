"""Add automatic enabled toggle to lab settings.

Revision ID: 094_add_automatic_enabled_to_lab_settings
Revises: 093_drop_semester_lab_settings
Create Date: 2026-04-16
"""

import sqlalchemy as sa

from alembic import op

revision = "094_add_automatic_enabled_to_lab_settings"
down_revision = "093_drop_semester_lab_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add automatic_enabled flag with safe default."""
    op.add_column(
        "lab_settings",
        sa.Column("automatic_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    """Remove automatic_enabled flag."""
    op.drop_column("lab_settings", "automatic_enabled")
