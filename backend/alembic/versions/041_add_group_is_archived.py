"""add group is_archived

Revision ID: 041
Revises: 040_add_lab_publish_fields
Create Date: 2026-01-07

"""
from alembic import op
import sqlalchemy as sa

revision = '041'
down_revision = '040_add_lab_publish_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('groups', sa.Column('is_archived', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    op.drop_column('groups', 'is_archived')
