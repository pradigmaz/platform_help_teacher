"""Add index for lab visibility queries.

Revision ID: 068_add_lesson_visibility_index
Revises: 067_lab_deadline_lessons
Create Date: 2026-01-12

Индекс для ускорения запросов видимости лаб по расписанию:
- get_batch_visibility_info
- get_visible_lab_numbers_by_subject
"""

from alembic import op


revision = "068_add_lesson_visibility_index"
down_revision = "067_deadline_lessons"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_lessons_visibility",
        "lessons",
        ["group_id", "lesson_type", "subject_id", "work_number", "date"],
        postgresql_where="is_cancelled = false AND work_number IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_index("idx_lessons_visibility", table_name="lessons")
