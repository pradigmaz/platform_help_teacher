"""Add created_by_id to lectures for IDOR protection

Revision ID: 060_add_created_by
Revises: 055
Create Date: 2026-01-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '060'
down_revision: Union[str, None] = '055'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add created_by_id column to lectures
    op.add_column(
        'lectures',
        sa.Column(
            'created_by_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment='User who created the lecture (for IDOR protection)'
        )
    )
    
    # Add index for faster ownership lookups
    op.create_index(
        'idx_lectures_created_by_id',
        'lectures',
        ['created_by_id']
    )
    
    # Add created_by_id to labs table
    op.add_column(
        'labs',
        sa.Column(
            'created_by_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment='User who created the lab (for IDOR protection)'
        )
    )
    
    op.create_index(
        'idx_labs_created_by_id',
        'labs',
        ['created_by_id']
    )
    
    # Add created_by_id to notes table
    op.add_column(
        'notes',
        sa.Column(
            'created_by_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment='User who created the note (for IDOR protection)'
        )
    )
    
    op.create_index(
        'idx_notes_created_by_id',
        'notes',
        ['created_by_id']
    )


def downgrade() -> None:
    op.drop_index('idx_notes_created_by_id', table_name='notes')
    op.drop_column('notes', 'created_by_id')
    
    op.drop_index('idx_labs_created_by_id', table_name='labs')
    op.drop_column('labs', 'created_by_id')
    
    op.drop_index('idx_lectures_created_by_id', table_name='lectures')
    op.drop_column('lectures', 'created_by_id')
