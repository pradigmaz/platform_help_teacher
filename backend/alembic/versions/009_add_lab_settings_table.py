"""Add global lab_settings table

Revision ID: 009_lab_settings_table
Revises: 008_add_lab_settings
Create Date: 2024-12-22

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '009_lab_settings_table'
down_revision: Union[str, None] = '008_add_lab_settings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum gradingscale уже создан в миграции 008
    op.create_table(
        'lab_settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('labs_count', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('grading_scale', sa.String(10), nullable=False, server_default='10'),
        sa.Column('default_max_grade', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('lab_settings')
