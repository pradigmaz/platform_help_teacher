"""Add unique constraint on submissions (user_id, lab_id)

Revision ID: 072_submission_unique
Revises: 071_feedback_attachments
Create Date: 2026-01-14

Prevents duplicate submissions for the same user+lab combination.
Before running: delete existing duplicates with SQL:

DELETE FROM submissions s1
USING submissions s2
WHERE s1.user_id = s2.user_id 
  AND s1.lab_id = s2.lab_id 
  AND s1.created_at < s2.created_at;
"""
from alembic import op


revision = "072_submission_unique"
down_revision = "071_feedback_attachments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_submission_user_lab",
        "submissions",
        ["user_id", "lab_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_submission_user_lab", "submissions", type_="unique")
