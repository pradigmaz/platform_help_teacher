"""add work and work_submission tables

Revision ID: 015_add_work_tables
Revises: 014_varchar_to_text
Create Date: 2024-12-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '015_add_work_tables'
down_revision: Union[str, None] = '014_varchar_to_text'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create WorkType enum first
    op.execute("CREATE TYPE worktype AS ENUM ('TEST', 'INDEPENDENT_WORK', 'COLLOQUIUM', 'FINAL_PROJECT')")

    # Create works table
    op.create_table(
        'works',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('work_type', postgresql.ENUM('TEST', 'INDEPENDENT_WORK', 'COLLOQUIUM', 'FINAL_PROJECT', name='worktype', create_type=False), nullable=False),
        sa.Column('max_grade', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('s3_key', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('length(title) <= 200', name='ck_works_title_len'),
        sa.CheckConstraint('length(s3_key) <= 500', name='ck_works_s3_key_len'),
        sa.CheckConstraint('max_grade > 0 AND max_grade <= 100', name='ck_works_max_grade'),
    )
    op.create_index('ix_works_work_type', 'works', ['work_type'])

    # Create work_submissions table
    op.create_table(
        'work_submissions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('work_id', sa.UUID(), nullable=False),
        sa.Column('grade', sa.Integer(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('s3_key', sa.String(500), nullable=True),
        sa.Column('is_manual', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['work_id'], ['works.id'], ondelete='CASCADE'),
        sa.CheckConstraint('(is_manual IS TRUE) OR (s3_key IS NOT NULL)', name='ck_work_sub_file_required'),
        sa.CheckConstraint('(grade IS NULL) OR (grade >= 0 AND grade <= 100)', name='ck_work_sub_grade_range'),
    )
    op.create_index('ix_work_submissions_user_id', 'work_submissions', ['user_id'])
    op.create_index('ix_work_submissions_work_id', 'work_submissions', ['work_id'])


def downgrade() -> None:
    op.drop_index('ix_work_submissions_work_id', 'work_submissions')
    op.drop_index('ix_work_submissions_user_id', 'work_submissions')
    op.drop_table('work_submissions')
    
    op.drop_index('ix_works_work_type', 'works')
    op.drop_table('works')
    
    # Drop enum
    work_type_enum = postgresql.ENUM('TEST', 'INDEPENDENT_WORK', 'COLLOQUIUM', 'FINAL_PROJECT', name='worktype')
    work_type_enum.drop(op.get_bind(), checkfirst=True)
