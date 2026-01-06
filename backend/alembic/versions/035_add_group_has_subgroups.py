"""Add has_subgroups to groups table

Revision ID: 035_group_has_subgroups
Revises: 034_group_invite_code
Create Date: 2026-01-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '035_group_has_subgroups'
down_revision: Union[str, None] = '034_group_invite_code'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('groups', sa.Column('has_subgroups', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    op.drop_column('groups', 'has_subgroups')
