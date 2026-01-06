"""Add teacher_settings column to users table

Revision ID: 032_teacher_settings
Revises: 031_teacher_contacts
Create Date: 2026-01-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '032_teacher_settings'
down_revision = '031_teacher_contacts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'teacher_settings',
            JSONB,
            nullable=False,
            server_default='{"hide_previous_semester": true}'
        )
    )


def downgrade() -> None:
    op.drop_column('users', 'teacher_settings')
