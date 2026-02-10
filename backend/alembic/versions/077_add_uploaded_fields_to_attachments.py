"""Add is_uploaded and uploaded_at to feedback_attachments

Revision ID: 077_add_uploaded_fields_to_attachments
Revises: 076_add_deadline_extensions
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "077_uploaded_fields"
down_revision = "076_deadline_extensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "feedback_attachments",
        sa.Column("is_uploaded", sa.Boolean, nullable=False, server_default="false"),
    )
    op.add_column(
        "feedback_attachments",
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("feedback_attachments", "uploaded_at")
    op.drop_column("feedback_attachments", "is_uploaded")
