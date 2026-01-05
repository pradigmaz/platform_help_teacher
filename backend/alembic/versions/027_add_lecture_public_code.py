"""add public_code to lectures

Revision ID: 027_lecture_public_code
Revises: 026_add_notes
Create Date: 2026-01-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '027_lecture_public_code'
down_revision: Union[str, None] = '026_add_notes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'lectures',
        sa.Column('public_code', sa.String(8), nullable=True, unique=True)
    )
    op.create_index(
        'idx_lectures_public_code',
        'lectures',
        ['public_code'],
        unique=True,
        postgresql_where=sa.text('public_code IS NOT NULL')
    )


def downgrade() -> None:
    op.drop_index('idx_lectures_public_code', table_name='lectures')
    op.drop_column('lectures', 'public_code')
