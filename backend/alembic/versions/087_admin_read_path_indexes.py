"""Add read-path indexes for admin aggregate views.

Revision ID: 087_admin_read_path_indexes
Revises: 086_add_activity_subject_scope
Create Date: 2026-03-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "087_admin_read_path_indexes"
down_revision = "086_add_activity_subject_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_lessons_group_subject_date_active",
        "lessons",
        ["group_id", "subject_id", "date"],
        unique=False,
        postgresql_where=sa.text("is_cancelled = false"),
    )
    op.create_index(
        "idx_attendance_group_lesson",
        "attendance",
        ["group_id", "lesson_id"],
        unique=False,
    )
    op.create_index(
        "idx_users_group_role_active",
        "users",
        ["group_id", "role", "is_active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_users_group_role_active", table_name="users")
    op.drop_index("idx_attendance_group_lesson", table_name="attendance")
    op.drop_index("idx_lessons_group_subject_date_active", table_name="lessons")
