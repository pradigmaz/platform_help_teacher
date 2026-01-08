"""Add rate_limit_warnings table

Revision ID: 061_rate_limit_warnings
Revises: 060_add_created_by
Create Date: 2026-01-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '061_rate_limit_warnings'
down_revision = '060'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'rate_limit_warnings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('fingerprint_hash', sa.String(64), nullable=True),
        sa.Column('warning_level', sa.String(20), nullable=False),
        sa.Column('violation_count', sa.Integer, nullable=False),
        sa.Column('message', sa.Text, nullable=True),
        sa.Column('ban_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('unbanned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('unbanned_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('unban_reason', sa.Text, nullable=True),
        sa.Column('admin_notified', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Индексы
    op.create_index('idx_rlw_user_id', 'rate_limit_warnings', ['user_id'])
    op.create_index('idx_rlw_ip_address', 'rate_limit_warnings', ['ip_address'])
    op.create_index('idx_rlw_fingerprint_hash', 'rate_limit_warnings', ['fingerprint_hash'])
    op.create_index('idx_rlw_user_created', 'rate_limit_warnings', ['user_id', 'created_at'])
    op.create_index('idx_rlw_ip_created', 'rate_limit_warnings', ['ip_address', 'created_at'])
    
    # Частичный индекс для активных банов
    op.execute("""
        CREATE INDEX idx_rlw_active_bans 
        ON rate_limit_warnings (ban_until) 
        WHERE ban_until IS NOT NULL AND unbanned_at IS NULL
    """)


def downgrade() -> None:
    op.drop_index('idx_rlw_active_bans', table_name='rate_limit_warnings')
    op.drop_index('idx_rlw_ip_created', table_name='rate_limit_warnings')
    op.drop_index('idx_rlw_user_created', table_name='rate_limit_warnings')
    op.drop_index('idx_rlw_fingerprint_hash', table_name='rate_limit_warnings')
    op.drop_index('idx_rlw_ip_address', table_name='rate_limit_warnings')
    op.drop_index('idx_rlw_user_id', table_name='rate_limit_warnings')
    op.drop_table('rate_limit_warnings')
