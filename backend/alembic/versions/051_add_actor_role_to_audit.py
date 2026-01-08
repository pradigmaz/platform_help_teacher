"""Add actor_role column to student_audit_log

Revision ID: 051_add_actor_role
Revises: 050_add_backup_settings
Create Date: 2026-01-08

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '051_add_actor_role'
down_revision: Union[str, None] = '050_add_backup_settings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add actor_role column with default 'student' for existing records
    op.add_column(
        'student_audit_log',
        sa.Column('actor_role', sa.String(20), nullable=False, server_default='student')
    )
    
    # Add index for filtering by role
    op.create_index(
        'idx_student_audit_actor_role',
        'student_audit_log',
        ['actor_role']
    )


def downgrade() -> None:
    op.drop_index('idx_student_audit_actor_role', table_name='student_audit_log')
    op.drop_column('student_audit_log', 'actor_role')
