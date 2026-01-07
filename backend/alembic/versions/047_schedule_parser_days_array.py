"""change day_of_week to days_of_week array

Revision ID: 047
Revises: 046_add_settings_audit_log
Create Date: 2026-01-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = '047'
down_revision = '44dd67787045'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Добавляем новую колонку days_of_week как массив
    op.add_column(
        'schedule_parser_configs',
        sa.Column('days_of_week', ARRAY(sa.Integer), nullable=True)
    )
    
    # 2. Мигрируем данные: day_of_week -> days_of_week (как массив из одного элемента)
    op.execute(
        "UPDATE schedule_parser_configs SET days_of_week = ARRAY[day_of_week] WHERE day_of_week IS NOT NULL"
    )
    
    # 3. Устанавливаем default для новых записей
    op.alter_column(
        'schedule_parser_configs',
        'days_of_week',
        server_default='{6}',  # воскресенье по умолчанию
        nullable=False
    )
    
    # 4. Удаляем старую колонку
    op.drop_column('schedule_parser_configs', 'day_of_week')


def downgrade() -> None:
    # 1. Добавляем обратно day_of_week
    op.add_column(
        'schedule_parser_configs',
        sa.Column('day_of_week', sa.Integer, nullable=True)
    )
    
    # 2. Мигрируем данные: берём первый элемент массива
    op.execute(
        "UPDATE schedule_parser_configs SET day_of_week = days_of_week[1] WHERE days_of_week IS NOT NULL"
    )
    
    # 3. Устанавливаем default
    op.alter_column(
        'schedule_parser_configs',
        'day_of_week',
        server_default='6',
        nullable=False
    )
    
    # 4. Удаляем days_of_week
    op.drop_column('schedule_parser_configs', 'days_of_week')
