"""Add teacher contacts columns to users table

Revision ID: 031_teacher_contacts
Revises: 030_group_reports
Create Date: 2026-01-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '031_teacher_contacts'
down_revision: Union[str, None] = '030_group_reports'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add contacts JSONB column with default empty object
    op.add_column(
        'users',
        sa.Column(
            'contacts',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default='{}'
        )
    )
    
    # Add contact_visibility JSONB column with default empty object
    op.add_column(
        'users',
        sa.Column(
            'contact_visibility',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default='{}'
        )
    )


def downgrade() -> None:
    op.drop_column('users', 'contact_visibility')
    op.drop_column('users', 'contacts')
