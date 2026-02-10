"""Add notification settings table

Revision ID: 074_add_notification_settings
Revises: 073_add_announcements
Create Date: 2026-01-17

"""
from alembic import op
import sqlalchemy as sa

revision = '074_notification_settings'
down_revision = '073_add_announcements'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'notification_settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('channel_telegram', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('channel_vk', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('channel_web', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notify_announcements', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    op.create_index('ix_notification_settings_user_id', 'notification_settings', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_notification_settings_user_id', table_name='notification_settings')
    op.drop_table('notification_settings')
