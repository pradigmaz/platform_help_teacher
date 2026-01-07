"""Add READY status to submissionstatus enum

Revision ID: 039_add_ready_status_enum
Revises: 038_extend_labs_submissions
Create Date: 2026-01-07

"""
from typing import Sequence, Union
from alembic import op

revision: str = '039_add_ready_status_enum'
down_revision: Union[str, None] = '038_extend_labs_submissions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE submissionstatus ADD VALUE IF NOT EXISTS 'READY'")


def downgrade() -> None:
    pass
