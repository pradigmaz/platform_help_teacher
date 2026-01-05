"""Make attestation_settings global (remove group_id)

Revision ID: 011_global_attestation_settings
Revises: 010_attestation_settings
Create Date: 2024-12-23

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '011_global_attestation_settings'
down_revision: Union[str, None] = '010_attestation_settings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Удаляем старые данные (если есть)
    op.execute("DELETE FROM attestation_settings")
    
    # 2. Удаляем индекс по group_id
    op.drop_index('ix_attestation_settings_group_id', table_name='attestation_settings')
    
    # 3. Удаляем constraint уникальности group_id + attestation_type
    op.drop_constraint('uq_group_attestation', 'attestation_settings', type_='unique')
    
    # 4. Удаляем foreign key на groups
    op.drop_constraint('attestation_settings_group_id_fkey', 'attestation_settings', type_='foreignkey')
    
    # 5. Удаляем колонку group_id
    op.drop_column('attestation_settings', 'group_id')
    
    # 6. Добавляем новый constraint уникальности только по attestation_type
    op.create_unique_constraint('uq_attestation_type', 'attestation_settings', ['attestation_type'])


def downgrade() -> None:
    # 1. Удаляем constraint уникальности по attestation_type
    op.drop_constraint('uq_attestation_type', 'attestation_settings', type_='unique')
    
    # 2. Добавляем колонку group_id обратно
    op.add_column('attestation_settings', sa.Column('group_id', sa.UUID(), nullable=True))
    
    # 3. Удаляем данные без group_id
    op.execute("DELETE FROM attestation_settings WHERE group_id IS NULL")
    
    # 4. Делаем group_id NOT NULL
    op.alter_column('attestation_settings', 'group_id', nullable=False)
    
    # 5. Добавляем foreign key
    op.create_foreign_key(
        'attestation_settings_group_id_fkey',
        'attestation_settings', 'groups',
        ['group_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 6. Добавляем индекс
    op.create_index('ix_attestation_settings_group_id', 'attestation_settings', ['group_id'])
    
    # 7. Добавляем constraint уникальности
    op.create_unique_constraint('uq_group_attestation', 'attestation_settings', ['group_id', 'attestation_type'])
