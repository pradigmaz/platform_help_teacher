"""add user group_role index

Revision ID: 042
Revises: 041
Create Date: 2026-01-07

"""
from alembic import op

revision = '042'
down_revision = '041'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index('ix_users_group_role', 'users', ['group_id', 'role'])


def downgrade() -> None:
    op.drop_index('ix_users_group_role', table_name='users')
