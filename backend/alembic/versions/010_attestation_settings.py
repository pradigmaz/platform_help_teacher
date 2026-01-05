"""Add attestation_settings table

Revision ID: 010_attestation_settings
Revises: 009_lab_settings_table
Create Date: 2024-12-23

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '010_attestation_settings'
down_revision: Union[str, None] = '009_lab_settings_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'attestation_settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=False),
        sa.Column('attestation_type', sa.String(10), nullable=False),
        
        # Веса компонентов (должны суммироваться в 100)
        sa.Column('labs_weight', sa.Float(), nullable=False, server_default='60.0'),
        sa.Column('attendance_weight', sa.Float(), nullable=False, server_default='20.0'),
        sa.Column('activity_weight', sa.Float(), nullable=False, server_default='20.0'),
        
        # Настройки лабораторных работ
        sa.Column('required_labs_count', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('bonus_per_extra_lab', sa.Float(), nullable=False, server_default='0.4'),
        
        # Коэффициенты штрафов за просрочку
        sa.Column('soft_deadline_penalty', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('hard_deadline_penalty', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('soft_deadline_days', sa.Integer(), nullable=False, server_default='7'),
        
        # Настройки посещаемости - баллы за статусы
        sa.Column('present_points', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('late_points', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('excused_points', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('absent_points', sa.Float(), nullable=False, server_default='-0.1'),
        
        # Настройки активности
        sa.Column('activity_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('participation_points', sa.Float(), nullable=False, server_default='0.5'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('group_id', 'attestation_type', name='uq_group_attestation')
    )
    
    # Индекс для быстрого поиска по group_id
    op.create_index('ix_attestation_settings_group_id', 'attestation_settings', ['group_id'])


def downgrade() -> None:
    op.drop_index('ix_attestation_settings_group_id', table_name='attestation_settings')
    op.drop_table('attestation_settings')
