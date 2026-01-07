"""add parse_history table

Revision ID: 048
Revises: 047
Create Date: 2026-01-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '048'
down_revision = '047'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'parse_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('teacher_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('config_id', UUID(as_uuid=True), sa.ForeignKey('schedule_parser_configs.id'), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='running'),
        sa.Column('lessons_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lessons_updated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lessons_skipped', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conflicts_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
    )
    
    # Индексы
    op.create_index('idx_parse_history_teacher', 'parse_history', ['teacher_id'])
    op.create_index('idx_parse_history_started', 'parse_history', ['started_at'])


def downgrade() -> None:
    op.drop_index('idx_parse_history_started')
    op.drop_index('idx_parse_history_teacher')
    op.drop_table('parse_history')
