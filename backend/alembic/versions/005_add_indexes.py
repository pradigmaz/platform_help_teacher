"""Add indexes for performance

Revision ID: 005_add_indexes
Revises: 004_make_social_id_nullable
Create Date: 2025-12-21 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005_add_indexes'
down_revision: Union[str, None] = '004_make_social_id_nullable'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Индекс для быстрого поиска групп по имени
    op.create_index(op.f('ix_groups_name'), 'groups', ['name'], unique=False)
    # Индекс для быстрого поиска лекций по заголовку
    op.create_index(op.f('ix_lectures_title'), 'lectures', ['title'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_lectures_title'), table_name='lectures')
    op.drop_index(op.f('ix_groups_name'), table_name='groups')