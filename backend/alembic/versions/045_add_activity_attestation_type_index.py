"""Add index on activities.attestation_type

Revision ID: 045
Revises: 044
Create Date: 2026-01-07
"""
from alembic import op


revision = '045'
down_revision = '044'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index('ix_activities_attestation_type', 'activities', ['attestation_type'])


def downgrade() -> None:
    op.drop_index('ix_activities_attestation_type', 'activities')
