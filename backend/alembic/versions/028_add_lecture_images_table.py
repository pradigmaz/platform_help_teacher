"""add lecture_images table

Revision ID: 028_lecture_images
Revises: 027_lecture_public_code
Create Date: 2026-01-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '028_lecture_images'
down_revision: Union[str, None] = '027_lecture_public_code'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'lecture_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lecture_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lectures.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('storage_path', sa.String(512), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_lecture_images_lecture_id', 'lecture_images', ['lecture_id'])


def downgrade() -> None:
    op.drop_index('idx_lecture_images_lecture_id', table_name='lecture_images')
    op.drop_table('lecture_images')
