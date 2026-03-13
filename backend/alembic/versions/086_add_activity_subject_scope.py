"""Add optional subject scope to activities.

Revision ID: 086_add_activity_subject_scope
Revises: 085_add_submission_lesson_context
Create Date: 2026-03-13
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "086_add_activity_subject_scope"
down_revision = "085_add_submission_lesson_context"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("activities", sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_activities_subject_id", "activities", ["subject_id"], unique=False)
    op.create_foreign_key(
        "fk_activities_subject_id",
        "activities",
        "subjects",
        ["subject_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_activities_subject_id", "activities", type_="foreignkey")
    op.drop_index("ix_activities_subject_id", table_name="activities")
    op.drop_column("activities", "subject_id")
