"""Make social_id nullable

Revision ID: 004_make_social_id_nullable
Revises: 003_invite_code
Create Date: 2025-12-21 19:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004_make_social_id_nullable'
down_revision: Union[str, None] = '003_invite_code'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Делаем social_id необязательным
    op.alter_column('users', 'social_id',
               existing_type=sa.BIGINT(),
               nullable=True)

def downgrade() -> None:
    # Возвращаем ограничение NOT NULL
    # Внимание: если в базе есть NULL значения, откат упадет с ошибкой
    op.execute("DELETE FROM users WHERE social_id IS NULL") # Очистка перед откатом (опасно, но необходимо для целостности)
    op.alter_column('users', 'social_id',
               existing_type=sa.BIGINT(),
               nullable=False)