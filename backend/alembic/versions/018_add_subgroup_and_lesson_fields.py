"""add subgroup to users and lesson fields to submissions

Revision ID: 018_subgroup_lesson
Revises: 017_add_schedule_and_lessons
Create Date: 2024-12-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '018_subgroup_lesson'
down_revision: Union[str, None] = '017_add_schedule_and_lessons'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Добавляем subgroup в users
    op.add_column('users', sa.Column('subgroup', sa.Integer(), nullable=True))
    
    # 2. Добавляем lesson_date и lesson_number в submissions
    op.add_column('submissions', sa.Column('lesson_date', sa.Date(), nullable=True))
    op.add_column('submissions', sa.Column('lesson_number', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('submissions', 'lesson_number')
    op.drop_column('submissions', 'lesson_date')
    op.drop_column('users', 'subgroup')
