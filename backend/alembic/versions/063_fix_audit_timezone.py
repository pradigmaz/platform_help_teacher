"""Fix settings_audit_log created_at timezone

Revision ID: 063_fix_audit_timezone
Revises: 062_add_semester_start_date
Create Date: 2026-01-09

"""
from typing import Union
from alembic import op
import sqlalchemy as sa


revision: str = '063_fix_audit_timezone'
down_revision: Union[str, None] = '062_add_semester_start_date'
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # Изменяем колонку created_at на TIMESTAMP WITH TIME ZONE
    op.alter_column(
        'settings_audit_log',
        'created_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=False
    )


def downgrade() -> None:
    op.alter_column(
        'settings_audit_log',
        'created_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False
    )
