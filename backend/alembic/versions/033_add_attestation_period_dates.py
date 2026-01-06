"""Add period_start_date and period_end_date to attestation_settings

Revision ID: 033_add_attestation_period_dates
Revises: 032_add_teacher_settings
Create Date: 2026-01-06
"""
from alembic import op
import sqlalchemy as sa

revision = '033_add_attestation_period_dates'
down_revision = '032_teacher_settings'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('attestation_settings', sa.Column('period_start_date', sa.Date(), nullable=True))
    op.add_column('attestation_settings', sa.Column('period_end_date', sa.Date(), nullable=True))


def downgrade():
    op.drop_column('attestation_settings', 'period_end_date')
    op.drop_column('attestation_settings', 'period_start_date')
