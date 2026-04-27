"""Remove notes feature storage.

Revision ID: 102_remove_notes_feature
Revises: 101_add_group_subject_offering_policies
Create Date: 2026-04-27
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "102_remove_notes_feature"
down_revision = "101_add_group_subject_offering_policies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("group_reports", "show_notes")

    op.drop_index("idx_notes_created_by_id", table_name="notes")
    op.drop_index("idx_notes_entity", table_name="notes")
    op.drop_table("notes")


def downgrade() -> None:
    op.create_table(
        "notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False, index=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("color", sa.String(20), nullable=False, server_default="default"),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("idx_notes_entity", "notes", ["entity_type", "entity_id"])
    op.create_index("idx_notes_created_by_id", "notes", ["created_by_id"])

    op.add_column(
        "group_reports",
        sa.Column("show_notes", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
