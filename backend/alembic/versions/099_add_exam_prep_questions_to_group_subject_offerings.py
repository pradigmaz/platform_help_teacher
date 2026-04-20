"""Add exam prep questions to group subject offerings.

Revision ID: 099_add_exam_prep_questions_to_group_subject_offerings
Revises: 098_add_offering_scope_to_schedule_and_lessons
Create Date: 2026-04-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "099_add_exam_prep_questions_to_group_subject_offerings"
down_revision = "098_add_offering_scope_to_schedule_and_lessons"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "group_subject_offerings",
        sa.Column("exam_prep_questions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("group_subject_offerings", "exam_prep_questions")
