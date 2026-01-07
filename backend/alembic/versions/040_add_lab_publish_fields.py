"""Add publish fields to labs

Revision ID: 040_add_lab_publish_fields
Revises: 039_add_ready_status_enum
Create Date: 2026-01-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '040_add_lab_publish_fields'
down_revision: Union[str, None] = '039_add_ready_status_enum'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('labs', sa.Column('is_published', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('labs', sa.Column('public_code', sa.String(20), nullable=True))
    op.execute("UPDATE labs SET is_published = false WHERE is_published IS NULL")
    op.alter_column('labs', 'is_published', nullable=False)
    op.create_index('ix_labs_public_code', 'labs', ['public_code'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_labs_public_code', table_name='labs')
    op.drop_column('labs', 'public_code')
    op.drop_column('labs', 'is_published')
