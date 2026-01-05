"""Add invite_code to users table

Revision ID: 003_invite_code
Revises: 002_attendance_and_manual_grades
Create Date: 2025-01-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_invite_code'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('users', sa.Column('invite_code', sa.String(8), nullable=True))
    op.create_index('ix_users_invite_code', 'users', ['invite_code'], unique=True)

def downgrade() -> None:
    op.drop_index('ix_users_invite_code', table_name='users')
    op.drop_column('users', 'invite_code')
