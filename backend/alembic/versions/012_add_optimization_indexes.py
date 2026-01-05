"""Add optimization indexes

Revision ID: 012_add_optimization_indexes
Revises: 011_global_attestation_settings
Create Date: 2024-12-25
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '012_add_optimization_indexes'
down_revision: Union[str, None] = '011_global_attestation_settings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add index on Submission.user_id for fast student submission lookup
    op.create_index('ix_submissions_user_id', 'submissions', ['user_id'], unique=False, if_not_exists=True)
    
    # Note: Index on Attendance (student_id, date) is already covered by 
    # uq_attendance_student_date unique constraint created in migration 002


def downgrade() -> None:
    op.drop_index('ix_submissions_user_id', table_name='submissions')

