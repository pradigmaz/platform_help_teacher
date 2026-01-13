"""Add feedback_attachments table

Revision ID: 071_feedback_attachments
Revises: 070_add_expected_lessons_per_week
Create Date: 2026-01-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "071_feedback_attachments"
down_revision = "070"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feedback_attachments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("feedback_id", UUID(as_uuid=True), sa.ForeignKey("feedback.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_feedback_attachments_feedback_id", "feedback_attachments", ["feedback_id"])
    op.create_index("ix_feedback_status", "feedback", ["status"])


def downgrade() -> None:
    op.drop_index("ix_feedback_status", "feedback")
    op.drop_index("ix_feedback_attachments_feedback_id")
    op.drop_table("feedback_attachments")
