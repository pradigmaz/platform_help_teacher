"""split social_id to telegram_id and vk_id

Revision ID: 037_split_social_id
Revises: 036_student_transfers
Create Date: 2026-01-07

"""
from alembic import op
import sqlalchemy as sa

revision = '037_split_social_id'
down_revision = '036_student_transfers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Добавляем новые колонки
    op.add_column('users', sa.Column('telegram_id', sa.BigInteger(), nullable=True))
    op.add_column('users', sa.Column('vk_id', sa.BigInteger(), nullable=True))
    
    # 2. Мигрируем данные: social_id -> telegram_id (все текущие - это Telegram)
    op.execute("UPDATE users SET telegram_id = social_id WHERE social_id IS NOT NULL")
    
    # 3. Создаём индексы
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)
    op.create_index('ix_users_vk_id', 'users', ['vk_id'], unique=True)
    
    # 4. Удаляем старую колонку
    op.drop_index('ix_users_social_id', table_name='users')
    op.drop_column('users', 'social_id')


def downgrade() -> None:
    # 1. Восстанавливаем social_id
    op.add_column('users', sa.Column('social_id', sa.BigInteger(), nullable=True))
    
    # 2. Мигрируем обратно (берём telegram_id как основной)
    op.execute("UPDATE users SET social_id = telegram_id WHERE telegram_id IS NOT NULL")
    
    # 3. Индекс
    op.create_index('ix_users_social_id', 'users', ['social_id'], unique=True)
    
    # 4. Удаляем новые колонки
    op.drop_index('ix_users_vk_id', table_name='users')
    op.drop_index('ix_users_telegram_id', table_name='users')
    op.drop_column('users', 'vk_id')
    op.drop_column('users', 'telegram_id')
