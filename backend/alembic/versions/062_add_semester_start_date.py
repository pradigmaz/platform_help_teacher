"""Add semester_start_date to attestation_settings

Revision ID: 062_add_semester_start_date
Revises: 061_rate_limit_warnings
Create Date: 2026-01-09

"""
from typing import Union
from alembic import op
import sqlalchemy as sa


revision: str = '062_add_semester_start_date'
down_revision: Union[str, None] = '061_rate_limit_warnings'
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.add_column(
        'attestation_settings',
        sa.Column('semester_start_date', sa.Date(), nullable=True,
                  comment='Дата начала семестра для автовычисления периодов аттестации')
    )


def downgrade() -> None:
    op.drop_column('attestation_settings', 'semester_start_date')
