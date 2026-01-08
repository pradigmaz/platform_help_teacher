"""Add backup_settings table

Revision ID: 050_add_backup_settings
Revises: 049_add_student_audit_log
Create Date: 2026-01-08

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '050_add_backup_settings'
down_revision: Union[str, None] = '049'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'backup_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('schedule_hour', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('schedule_minute', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('retention_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('max_backups', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('storage_bucket', sa.String(100), nullable=False, server_default='edu-backups'),
        sa.Column('notify_on_success', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notify_on_failure', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Insert default settings
    op.execute("""
        INSERT INTO backup_settings (id, enabled, schedule_hour, schedule_minute, retention_days, max_backups, storage_bucket, notify_on_success, notify_on_failure)
        VALUES (1, true, 3, 0, 30, 10, 'edu-backups', false, true)
    """)


def downgrade() -> None:
    op.drop_table('backup_settings')
