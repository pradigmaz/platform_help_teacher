"""Update backup settings defaults to 17:00

Revision ID: 055_update_backup_defaults
Revises: 054_add_correlation_id
Create Date: 2026-01-08

"""
from typing import Sequence, Union
from alembic import op


revision: str = '055'
down_revision: Union[str, None] = '054'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update server defaults
    op.alter_column('backup_settings', 'schedule_hour', server_default='17')
    
    # Update existing row if still at old default
    op.execute("""
        UPDATE backup_settings 
        SET schedule_hour = 17 
        WHERE id = 1 AND schedule_hour = 3
    """)


def downgrade() -> None:
    op.alter_column('backup_settings', 'schedule_hour', server_default='3')
    op.execute("""
        UPDATE backup_settings 
        SET schedule_hour = 3 
        WHERE id = 1 AND schedule_hour = 17
    """)
