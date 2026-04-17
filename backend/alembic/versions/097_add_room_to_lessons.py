"""Add parsed room display value to lessons.

Revision ID: 097_add_room_to_lessons
Revises: 096_normalize_group_subject_offering_semesters
Create Date: 2026-04-17
"""

import sqlalchemy as sa

from alembic import op

revision = "097_add_room_to_lessons"
down_revision = "096_normalize_group_subject_offering_semesters"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _has_column("lessons", "room"):
        op.add_column("lessons", sa.Column("room", sa.String(50), nullable=True))


def downgrade() -> None:
    if _has_column("lessons", "room"):
        op.drop_column("lessons", "room")
