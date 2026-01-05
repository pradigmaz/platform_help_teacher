"""Add subject_id to lectures

Revision ID: 029_lecture_subject
Revises: 028_lecture_images
Create Date: 2026-01-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '029_lecture_subject'
down_revision: Union[str, None] = '028_lecture_images'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add subject_id column to lectures
    op.add_column(
        'lectures',
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_lectures_subject',
        'lectures', 'subjects',
        ['subject_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add index for subject_id
    op.create_index('idx_lectures_subject_id', 'lectures', ['subject_id'])


def downgrade() -> None:
    op.drop_index('idx_lectures_subject_id', 'lectures')
    op.drop_constraint('fk_lectures_subject', 'lectures', type_='foreignkey')
    op.drop_column('lectures', 'subject_id')
