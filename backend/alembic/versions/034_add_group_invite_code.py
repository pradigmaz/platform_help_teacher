"""Add invite_code to groups table

Revision ID: 034_group_invite_code
Revises: 033_add_attestation_period_dates
Create Date: 2026-01-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '034_group_invite_code'
down_revision: Union[str, None] = '033_add_attestation_period_dates'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('groups', sa.Column('invite_code', sa.Text(), nullable=True))
    op.create_index('ix_groups_invite_code', 'groups', ['invite_code'], unique=True)
    op.create_check_constraint('ck_groups_invite_code_len', 'groups', 'length(invite_code) <= 8')


def downgrade() -> None:
    op.drop_constraint('ck_groups_invite_code_len', 'groups', type_='check')
    op.drop_index('ix_groups_invite_code', table_name='groups')
    op.drop_column('groups', 'invite_code')
