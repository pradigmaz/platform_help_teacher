"""Add lesson_id to submissions for canonical lab acceptance context.

Revision ID: 085_add_submission_lesson_context
Revises: 084_cleanup_duplicate_lesson_grades
Create Date: 2026-03-13
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "085_add_submission_lesson_context"
down_revision = "084_cleanup_duplicate_lesson_grades"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("submissions", sa.Column("lesson_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_submissions_lesson_id",
        "submissions",
        "lessons",
        ["lesson_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_submissions_lesson_id", "submissions", type_="foreignkey")
    op.drop_column("submissions", "lesson_id")
