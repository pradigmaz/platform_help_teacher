"""Add schedule parser config and conflicts tables

Revision ID: 024_add_schedule_parser_tables
Revises: 023_update_lessons_subject_id
Create Date: 2026-01-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '024_add_schedule_parser_tables'
down_revision = '023_update_lessons_subject_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create conflict_type enum
    op.execute("CREATE TYPE conflict_type_enum AS ENUM ('changed', 'deleted')")
    
    # Create schedule_parser_configs table
    op.create_table(
        'schedule_parser_configs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('teacher_id', sa.UUID(), nullable=False),
        sa.Column('teacher_name', sa.String(100), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('day_of_week', sa.Integer(), nullable=False, server_default='6'),
        sa.Column('run_time', sa.String(5), nullable=False, server_default='20:00'),
        sa.Column('parse_days_ahead', sa.Integer(), nullable=False, server_default='14'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id']),
        sa.UniqueConstraint('teacher_id')
    )
    
    # Create schedule_conflicts table
    op.create_table(
        'schedule_conflicts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('lesson_id', sa.UUID(), nullable=False),
        sa.Column('conflict_type', sa.String(20), nullable=False),
        sa.Column('old_data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('new_data', postgresql.JSONB(), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolution', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'])
    )
    
    op.create_index('idx_schedule_conflicts_lesson', 'schedule_conflicts', ['lesson_id'])
    op.create_index('idx_schedule_conflicts_resolved', 'schedule_conflicts', ['resolved'])


def downgrade() -> None:
    op.drop_index('idx_schedule_conflicts_resolved')
    op.drop_index('idx_schedule_conflicts_lesson')
    op.drop_table('schedule_conflicts')
    op.drop_table('schedule_parser_configs')
    op.execute('DROP TYPE IF EXISTS conflict_type_enum')
