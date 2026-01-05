"""add ended_early to lessons

Revision ID: 025_add_ended_early
Revises: 024_add_schedule_parser_tables
Create Date: 2026-01-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '025_add_ended_early'
down_revision: Union[str, None] = '024_add_schedule_parser_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('lessons', sa.Column('ended_early', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('lessons', 'ended_early')
