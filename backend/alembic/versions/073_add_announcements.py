"""Add announcements table

Revision ID: 073_add_announcements
Revises: 072_add_submission_unique_constraint
Create Date: 2026-01-17

"""

from alembic import op
import sqlalchemy as sa

revision = "073_add_announcements"
down_revision = "072_submission_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "announcements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("is_draft", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_announcements_created_by", "announcements", ["created_by"])
    op.create_index("ix_announcements_is_draft", "announcements", ["is_draft"])
    op.create_index("ix_announcements_published_at", "announcements", ["published_at"])


def downgrade() -> None:
    op.drop_index("ix_announcements_published_at", table_name="announcements")
    op.drop_index("ix_announcements_is_draft", table_name="announcements")
    op.drop_index("ix_announcements_created_by", table_name="announcements")
    op.drop_table("announcements")
