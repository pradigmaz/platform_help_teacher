"""Extend labs and submissions for new lab editor format

Revision ID: 038_extend_labs_submissions
Revises: 037_split_social_id
Create Date: 2026-01-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '038_extend_labs_submissions'
down_revision: Union[str, None] = '037_split_social_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === Labs table extensions ===
    
    # Add number column
    op.add_column('labs', sa.Column('number', sa.Integer(), nullable=True))
    op.execute("UPDATE labs SET number = 1 WHERE number IS NULL")
    op.alter_column('labs', 'number', nullable=False)
    
    # Add subject_id FK
    op.add_column('labs', sa.Column('subject_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_labs_subject_id', 'labs', 'subjects',
        ['subject_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_labs_subject_id', 'labs', ['subject_id'])
    
    # Add lesson_id FK
    op.add_column('labs', sa.Column('lesson_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_labs_lesson_id', 'labs', 'lessons',
        ['lesson_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add content fields
    op.add_column('labs', sa.Column('topic', sa.Text(), nullable=True))
    op.add_column('labs', sa.Column('goal', sa.Text(), nullable=True))
    op.add_column('labs', sa.Column('formatting_guide', sa.Text(), nullable=True))
    op.add_column('labs', sa.Column('theory_content', postgresql.JSONB(), nullable=True))
    op.add_column('labs', sa.Column('practice_content', postgresql.JSONB(), nullable=True))
    op.add_column('labs', sa.Column('variants', postgresql.JSONB(), nullable=True))
    op.add_column('labs', sa.Column('questions', postgresql.JSONB(), nullable=True))
    
    # Add is_sequential flag
    op.add_column('labs', sa.Column('is_sequential', sa.Boolean(), nullable=True, server_default='true'))
    op.execute("UPDATE labs SET is_sequential = true WHERE is_sequential IS NULL")
    op.alter_column('labs', 'is_sequential', nullable=False)
    
    # Add constraints and indexes
    op.create_check_constraint('ck_labs_number_positive', 'labs', 'number > 0')
    op.create_index('idx_labs_subject_number', 'labs', ['subject_id', 'number'])
    
    # Change default max_grade from 10 to 5
    op.alter_column('labs', 'max_grade', server_default='5')
    
    # === Submissions table extensions ===
    
    # Add variant_number
    op.add_column('submissions', sa.Column('variant_number', sa.Integer(), nullable=True))
    
    # Add ready_at timestamp
    op.add_column('submissions', sa.Column('ready_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add accepted_at timestamp
    op.add_column('submissions', sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True))
    
    # Change default is_manual to true
    op.alter_column('submissions', 'is_manual', server_default='true')
    op.execute("UPDATE submissions SET is_manual = true WHERE is_manual = false")


def downgrade() -> None:
    # === Submissions table ===
    op.drop_column('submissions', 'accepted_at')
    op.drop_column('submissions', 'ready_at')
    op.drop_column('submissions', 'variant_number')
    op.alter_column('submissions', 'is_manual', server_default='false')
    
    # === Labs table ===
    op.drop_index('idx_labs_subject_number', table_name='labs')
    op.drop_constraint('ck_labs_number_positive', 'labs', type_='check')
    
    op.drop_column('labs', 'is_sequential')
    op.drop_column('labs', 'questions')
    op.drop_column('labs', 'variants')
    op.drop_column('labs', 'practice_content')
    op.drop_column('labs', 'theory_content')
    op.drop_column('labs', 'formatting_guide')
    op.drop_column('labs', 'goal')
    op.drop_column('labs', 'topic')
    
    op.drop_constraint('fk_labs_lesson_id', 'labs', type_='foreignkey')
    op.drop_column('labs', 'lesson_id')
    
    op.drop_index('ix_labs_subject_id', table_name='labs')
    op.drop_constraint('fk_labs_subject_id', 'labs', type_='foreignkey')
    op.drop_column('labs', 'subject_id')
    
    op.drop_column('labs', 'number')
    op.alter_column('labs', 'max_grade', server_default='10')
