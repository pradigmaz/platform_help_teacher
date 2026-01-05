"""Update existing lessons with subject_id based on topic

Revision ID: 023_update_lessons_subject_id
Revises: 022_create_attendance_table
Create Date: 2026-01-03
"""
from typing import Union
from alembic import op

revision: str = '023_update_lessons_subject_id'
down_revision: Union[str, None] = '022_create_attendance_table'
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # Update lessons.subject_id based on matching topic with subjects.name
    op.execute("""
        UPDATE lessons l
        SET subject_id = s.id
        FROM subjects s
        WHERE l.topic = s.name
        AND l.subject_id IS NULL
    """)


def downgrade() -> None:
    # Clear subject_id
    op.execute("UPDATE lessons SET subject_id = NULL")
