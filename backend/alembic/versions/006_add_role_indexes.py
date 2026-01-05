"""Add indexes for role and is_published

Revision ID: 006_add_role_indexes
Revises: 005_add_indexes
Create Date: 2025-12-22 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = '006_add_role_indexes'
down_revision: Union[str, None] = '005_add_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Index for filtering users by role (admin panel, statistics)
    op.create_index('ix_users_role', 'users', ['role'], unique=False)
    # Index for filtering published lectures
    op.create_index('ix_lectures_is_published', 'lectures', ['is_published'], unique=False)
    # Composite index for "students in group" queries
    op.create_index('ix_users_group_role', 'users', ['group_id', 'role'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_users_group_role', table_name='users')
    op.drop_index('ix_lectures_is_published', table_name='lectures')
    op.drop_index('ix_users_role', table_name='users')
