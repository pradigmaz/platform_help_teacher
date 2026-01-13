"""Add expected_lessons_per_week to attestation_settings

Revision ID: 070
Revises: 069_add_feedback_table
Create Date: 2026-01-13
"""
from alembic import op
import sqlalchemy as sa

revision = '070_add_expected_lessons_per_week'
down_revision = '069_add_feedback_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'attestation_settings',
        sa.Column('expected_lessons_per_week', sa.Integer(), nullable=False, server_default='2')
    )


def downgrade() -> None:
    op.drop_column('attestation_settings', 'expected_lessons_per_week')
