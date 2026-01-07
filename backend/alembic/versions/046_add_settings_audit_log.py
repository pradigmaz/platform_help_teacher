"""Add settings_audit_log table

Revision ID: 046
Revises: 045
Create Date: 2026-01-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '046'
down_revision: Union[str, None] = '045'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'settings_audit_log',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('settings_type', sa.String(50), nullable=False),
        sa.Column('settings_key', sa.String(50), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('old_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('changed_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('changed_by_id', sa.UUID(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['changed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы для быстрого поиска
    op.create_index('ix_settings_audit_log_settings_type', 'settings_audit_log', ['settings_type'])
    op.create_index('ix_settings_audit_log_settings_key', 'settings_audit_log', ['settings_key'])
    op.create_index('ix_settings_audit_log_created_at', 'settings_audit_log', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_settings_audit_log_created_at', table_name='settings_audit_log')
    op.drop_index('ix_settings_audit_log_settings_key', table_name='settings_audit_log')
    op.drop_index('ix_settings_audit_log_settings_type', table_name='settings_audit_log')
    op.drop_table('settings_audit_log')
