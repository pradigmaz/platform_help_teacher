"""Add missing last_run_at to schedule_parser_configs.

Revision ID: 089_add_schedule_parser_last_run_at
Revises: 088_pre_vps_db_reconciliation
Create Date: 2026-04-03
"""

import sqlalchemy as sa

from alembic import op

revision = "089_add_schedule_parser_last_run_at"
down_revision = "088_pre_vps_db_reconciliation"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _has_column("schedule_parser_configs", "last_run_at"):
        op.add_column("schedule_parser_configs", sa.Column("last_run_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    if _has_column("schedule_parser_configs", "last_run_at"):
        op.drop_column("schedule_parser_configs", "last_run_at")
