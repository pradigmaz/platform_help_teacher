"""
Рефакторинг дедлайнов лабораторных: datetime → количество пар.

- labs: убрать deadline, добавить deadline_5_lessons, deadline_4_lessons
- attestation_settings: убрать late_threshold_days, late_max_grade, very_late_max_grade
"""
from alembic import op
import sqlalchemy as sa


revision = '067_deadline_lessons'
down_revision = '066_add_absent_coef'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Добавляем новые поля в labs
    op.add_column('labs', sa.Column('deadline_5_lessons', sa.Integer(), nullable=True))
    op.add_column('labs', sa.Column('deadline_4_lessons', sa.Integer(), nullable=True))
    
    # 2. Удаляем старый deadline из labs
    op.drop_column('labs', 'deadline')
    
    # 3. Удаляем поля дедлайнов из attestation_settings
    op.drop_column('attestation_settings', 'late_threshold_days')
    op.drop_column('attestation_settings', 'late_max_grade')
    op.drop_column('attestation_settings', 'very_late_max_grade')


def downgrade() -> None:
    # 1. Возвращаем поля в attestation_settings
    op.add_column('attestation_settings', 
        sa.Column('late_threshold_days', sa.Integer(), nullable=False, server_default='7'))
    op.add_column('attestation_settings', 
        sa.Column('late_max_grade', sa.Integer(), nullable=False, server_default='4'))
    op.add_column('attestation_settings', 
        sa.Column('very_late_max_grade', sa.Integer(), nullable=False, server_default='3'))
    
    # 2. Возвращаем deadline в labs
    op.add_column('labs', 
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True))
    
    # 3. Удаляем новые поля
    op.drop_column('labs', 'deadline_5_lessons')
    op.drop_column('labs', 'deadline_4_lessons')
