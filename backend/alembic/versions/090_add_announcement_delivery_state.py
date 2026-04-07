"""Add delivery lifecycle fields to announcements.

Revision ID: 090_add_announcement_delivery_state
Revises: 089_add_schedule_parser_last_run_at
Create Date: 2026-04-07
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "090_add_announcement_delivery_state"
down_revision = "089_add_schedule_parser_last_run_at"
branch_labels = None
depends_on = None

SEND_STATUS_ENUM = sa.Enum(
    "not_sent",
    "sending",
    "sent",
    "failed",
    name="announcement_send_status_enum",
)


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    SEND_STATUS_ENUM.create(bind, checkfirst=True)

    if not _has_column("announcements", "send_status"):
        op.add_column(
            "announcements",
            sa.Column("send_status", SEND_STATUS_ENUM, nullable=False, server_default="not_sent"),
        )
    if not _has_column("announcements", "send_started_at"):
        op.add_column("announcements", sa.Column("send_started_at", sa.DateTime(timezone=True), nullable=True))
    if not _has_column("announcements", "sent_at"):
        op.add_column("announcements", sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True))
    if not _has_column("announcements", "sent_by"):
        op.add_column(
            "announcements",
            sa.Column("sent_by", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        )
    if not _has_column("announcements", "delivery_stats"):
        op.add_column("announcements", sa.Column("delivery_stats", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    if not _has_column("announcements", "delivery_error"):
        op.add_column("announcements", sa.Column("delivery_error", sa.Text(), nullable=True))

    if not _has_index("announcements", "ix_announcements_send_status"):
        op.create_index("ix_announcements_send_status", "announcements", ["send_status"])
    if not _has_index("announcements", "ix_announcements_sent_by"):
        op.create_index("ix_announcements_sent_by", "announcements", ["sent_by"])

    op.execute(
        """
        UPDATE announcements
        SET send_status = 'sent',
            sent_at = COALESCE(published_at, created_at)
        WHERE is_draft = FALSE
        """
    )


def downgrade() -> None:
    if _has_index("announcements", "ix_announcements_sent_by"):
        op.drop_index("ix_announcements_sent_by", table_name="announcements")
    if _has_index("announcements", "ix_announcements_send_status"):
        op.drop_index("ix_announcements_send_status", table_name="announcements")

    if _has_column("announcements", "delivery_error"):
        op.drop_column("announcements", "delivery_error")
    if _has_column("announcements", "delivery_stats"):
        op.drop_column("announcements", "delivery_stats")
    if _has_column("announcements", "sent_by"):
        op.drop_column("announcements", "sent_by")
    if _has_column("announcements", "sent_at"):
        op.drop_column("announcements", "sent_at")
    if _has_column("announcements", "send_started_at"):
        op.drop_column("announcements", "send_started_at")
    if _has_column("announcements", "send_status"):
        op.drop_column("announcements", "send_status")

    SEND_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
