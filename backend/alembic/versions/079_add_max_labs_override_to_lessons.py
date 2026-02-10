"""Add max_labs_override field to lessons table.

Allows manual override of the maximum number of labs that can be
defended during a single lesson. NULL means standard logic applies
(1 lab normally, 2 for EXCUSED attendance).

Revision ID: 079_add_max_labs_override_to_lessons
Revises: 078_fix_lesson_grade_null_constraint
Create Date: 2026-01-30
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "079_add_max_labs_override_to_lessons"
down_revision = "078_lesson_grade_null_fix"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add max_labs_override column
    op.add_column("lessons", sa.Column("max_labs_override", sa.Integer(), nullable=True))

    # Add check constraint
    op.create_check_constraint(
        "ck_lesson_max_labs_override",
        "lessons",
        "max_labs_override IS NULL OR (max_labs_override >= 1 AND max_labs_override <= 10)",
    )


def downgrade() -> None:
    # Drop check constraint
    op.drop_constraint("ck_lesson_max_labs_override", "lessons", type_="check")

    # Drop column
    op.drop_column("lessons", "max_labs_override")
