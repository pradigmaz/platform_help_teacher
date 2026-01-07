"""Add check constraint for lesson_grade range (2-5)

Revision ID: 044
Revises: 043
Create Date: 2026-01-07
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '044'
down_revision = '043'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем CheckConstraint для валидации оценок 2-5
    op.create_check_constraint(
        'ck_lesson_grade_range',
        'lesson_grades',
        'grade >= 2 AND grade <= 5'
    )


def downgrade() -> None:
    op.drop_constraint('ck_lesson_grade_range', 'lesson_grades', type_='check')
