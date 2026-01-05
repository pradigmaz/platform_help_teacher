"""Add onboarding_completed to users

Revision ID: 019_add_onboarding_completed
Revises: 018_subgroup_lesson
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa

revision: str = '019_add_onboarding_completed'
down_revision: str = '018_subgroup_lesson'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('users', sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default='false'))

def downgrade() -> None:
    op.drop_column('users', 'onboarding_completed')
