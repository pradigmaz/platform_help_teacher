"""add soft delete fields to labs and submissions

Revision ID: 043
Revises: 042
Create Date: 2026-01-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '043'
down_revision: Union[str, None] = '042'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add deleted_at to labs
    op.add_column(
        'labs',
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        'idx_labs_deleted_at',
        'labs',
        ['deleted_at'],
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    
    # Add deleted_at to submissions
    op.add_column(
        'submissions',
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        'idx_submissions_deleted_at',
        'submissions',
        ['deleted_at'],
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    
    # Add index on submission status for queue queries
    op.create_index('idx_submission_status', 'submissions', ['status'])
    op.create_index('idx_submission_status_ready_at', 'submissions', ['status', 'ready_at'])


def downgrade() -> None:
    op.drop_index('idx_submission_status_ready_at', table_name='submissions')
    op.drop_index('idx_submission_status', table_name='submissions')
    
    op.drop_index('idx_submissions_deleted_at', table_name='submissions')
    op.drop_column('submissions', 'deleted_at')
    
    op.drop_index('idx_labs_deleted_at', table_name='labs')
    op.drop_column('labs', 'deleted_at')
