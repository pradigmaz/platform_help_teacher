"""Add lab settings to groups

Revision ID: 008_add_lab_settings
Revises: fae5e62d371f
Create Date: 2024-12-22

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '008_add_lab_settings'
down_revision: Union[str, None] = 'fae5e62d371f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаём enum тип для системы оценивания (checkfirst для идемпотентности)
    from sqlalchemy import text
    conn = op.get_bind()
    result = conn.execute(text("SELECT 1 FROM pg_type WHERE typname = 'gradingscale'"))
    if not result.fetchone():
        grading_scale_enum = sa.Enum('FIVE', 'TEN', 'HUNDRED', name='gradingscale')
        grading_scale_enum.create(conn)
    
    # Добавляем колонки настроек лабораторных
    op.add_column('groups', sa.Column('labs_count', sa.Integer(), nullable=True))
    op.add_column('groups', sa.Column('grading_scale', sa.Enum('FIVE', 'TEN', 'HUNDRED', name='gradingscale'), nullable=True, server_default='TEN'))
    op.add_column('groups', sa.Column('default_max_grade', sa.Integer(), nullable=True, server_default='10'))


def downgrade() -> None:
    op.drop_column('groups', 'default_max_grade')
    op.drop_column('groups', 'grading_scale')
    op.drop_column('groups', 'labs_count')
    
    # Удаляем enum тип
    sa.Enum(name='gradingscale').drop(op.get_bind(), checkfirst=True)
