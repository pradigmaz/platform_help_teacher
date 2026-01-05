"""Add group_reports and report_views tables

Revision ID: 030_group_reports
Revises: 029_lecture_subject
Create Date: 2026-01-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '030_group_reports'
down_revision: Union[str, None] = '029_lecture_subject'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create group_reports table
    op.create_table(
        'group_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(8), unique=True, nullable=False),
        sa.Column('report_type', sa.String(20), nullable=False, server_default='full'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pin_hash', sa.String(128), nullable=True),
        sa.Column('show_names', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('show_grades', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('show_attendance', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('show_notes', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('show_rating', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('views_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Foreign keys for group_reports
    op.create_foreign_key(
        'fk_group_reports_group',
        'group_reports', 'groups',
        ['group_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_group_reports_creator',
        'group_reports', 'users',
        ['created_by'], ['id'],
        ondelete='CASCADE'
    )
    
    # Indexes for group_reports
    op.create_index('idx_group_reports_code', 'group_reports', ['code'], unique=True)
    op.create_index('idx_group_reports_group', 'group_reports', ['group_id'])
    op.create_index('idx_group_reports_creator', 'group_reports', ['created_by'])
    
    # Create report_views table
    op.create_table(
        'report_views',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('viewed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.String(512), nullable=True),
    )
    
    # Foreign key for report_views
    op.create_foreign_key(
        'fk_report_views_report',
        'report_views', 'group_reports',
        ['report_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Indexes for report_views
    op.create_index('idx_report_views_report', 'report_views', ['report_id'])
    op.create_index('idx_report_views_viewed_at', 'report_views', ['viewed_at'])


def downgrade() -> None:
    # Drop report_views
    op.drop_index('idx_report_views_viewed_at', 'report_views')
    op.drop_index('idx_report_views_report', 'report_views')
    op.drop_constraint('fk_report_views_report', 'report_views', type_='foreignkey')
    op.drop_table('report_views')
    
    # Drop group_reports
    op.drop_index('idx_group_reports_creator', 'group_reports')
    op.drop_index('idx_group_reports_group', 'group_reports')
    op.drop_index('idx_group_reports_code', 'group_reports')
    op.drop_constraint('fk_group_reports_creator', 'group_reports', type_='foreignkey')
    op.drop_constraint('fk_group_reports_group', 'group_reports', type_='foreignkey')
    op.drop_table('group_reports')
