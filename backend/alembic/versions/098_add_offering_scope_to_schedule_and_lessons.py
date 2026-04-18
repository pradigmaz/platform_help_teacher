"""Add offering scope to schedule items and lessons.

Revision ID: 098_add_offering_scope_to_schedule_and_lessons
Revises: 097_add_room_to_lessons
Create Date: 2026-04-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "098_add_offering_scope_to_schedule_and_lessons"
down_revision = "097_add_room_to_lessons"
branch_labels = None
depends_on = None


def _create_index(table_name: str, index_name: str, column_name: str) -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            op.create_index(index_name, table_name, [column_name], unique=False, postgresql_concurrently=True)
        return
    op.create_index(index_name, table_name, [column_name], unique=False)


def _drop_index(table_name: str, index_name: str) -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            op.drop_index(index_name, table_name=table_name, postgresql_concurrently=True)
        return
    op.drop_index(index_name, table_name=table_name)


def upgrade() -> None:
    op.add_column(
        "schedule_items",
        sa.Column("offering_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "lessons",
        sa.Column("offering_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_foreign_key(
        "fk_schedule_items_offering_id_group_subject_offerings",
        "schedule_items",
        "group_subject_offerings",
        ["offering_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_lessons_offering_id_group_subject_offerings",
        "lessons",
        "group_subject_offerings",
        ["offering_id"],
        ["id"],
        ondelete="SET NULL",
    )

    _create_index("schedule_items", "ix_schedule_items_offering_id", "offering_id")
    _create_index("lessons", "ix_lessons_offering_id", "offering_id")


def downgrade() -> None:
    _drop_index("lessons", "ix_lessons_offering_id")
    _drop_index("schedule_items", "ix_schedule_items_offering_id")

    op.drop_constraint("fk_lessons_offering_id_group_subject_offerings", "lessons", type_="foreignkey")
    op.drop_constraint(
        "fk_schedule_items_offering_id_group_subject_offerings",
        "schedule_items",
        type_="foreignkey",
    )

    op.drop_column("lessons", "offering_id")
    op.drop_column("schedule_items", "offering_id")
