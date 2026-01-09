"""Autobalance attestation - switch from absolute points to coefficients

Revision ID: 065_autobalance_attestation
Revises: 064_refactor_attestation
Create Date: 2026-01-09

Changes:
- Remove: grade_X_points (absolute points per grade)
- Remove: self_works_grade_X_points, colloquium_grade_X_points
- Remove: present_points, late_points, absent_points
- Remove: participation_points
- Remove: required_labs_count (replaced by labs_count_first/second)
- Add: grade_4_coef, grade_3_coef (coefficients, grade_5=1.0 fixed, grade_2=0.0 fixed)
- Add: labs_count_first, labs_count_second (work counts per attestation)
- Add: self_works_count, colloquium_count
- Add: late_coef (coefficient for late attendance)
- Rename: activity_weight -> activity_reserve (reserve for bonuses/penalties)
"""
from typing import Union
from alembic import op
import sqlalchemy as sa


revision: str = '065_autobalance_attestation'
down_revision: Union[str, None] = '064_refactor_attestation'
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # === УДАЛЕНИЕ АБСОЛЮТНЫХ БАЛЛОВ ===
    # Лабораторные
    op.drop_column('attestation_settings', 'grade_5_points')
    op.drop_column('attestation_settings', 'grade_4_points')
    op.drop_column('attestation_settings', 'grade_3_points')
    op.drop_column('attestation_settings', 'grade_2_points')
    op.drop_column('attestation_settings', 'required_labs_count')
    
    # Самостоятельные работы
    op.drop_column('attestation_settings', 'self_works_grade_5_points')
    op.drop_column('attestation_settings', 'self_works_grade_4_points')
    op.drop_column('attestation_settings', 'self_works_grade_3_points')
    op.drop_column('attestation_settings', 'self_works_grade_2_points')
    
    # Коллоквиум
    op.drop_column('attestation_settings', 'colloquium_grade_5_points')
    op.drop_column('attestation_settings', 'colloquium_grade_4_points')
    op.drop_column('attestation_settings', 'colloquium_grade_3_points')
    op.drop_column('attestation_settings', 'colloquium_grade_2_points')
    
    # Посещаемость (абсолютные баллы)
    op.drop_column('attestation_settings', 'present_points')
    op.drop_column('attestation_settings', 'late_points')
    op.drop_column('attestation_settings', 'absent_points')
    
    # Активность
    op.drop_column('attestation_settings', 'participation_points')
    
    # === ПЕРЕИМЕНОВАНИЕ ===
    op.alter_column('attestation_settings', 'activity_weight', 
                    new_column_name='activity_reserve')
    
    # === ДОБАВЛЕНИЕ КОЭФФИЦИЕНТОВ ===
    # Коэффициенты оценок (grade_5=1.0 и grade_2=0.0 фиксированы, не хранятся)
    op.add_column('attestation_settings', 
        sa.Column('grade_4_coef', sa.Float(), nullable=False, server_default='0.7'))
    op.add_column('attestation_settings', 
        sa.Column('grade_3_coef', sa.Float(), nullable=False, server_default='0.4'))
    
    # Количество работ
    op.add_column('attestation_settings', 
        sa.Column('labs_count_first', sa.Integer(), nullable=False, server_default='8'))
    op.add_column('attestation_settings', 
        sa.Column('labs_count_second', sa.Integer(), nullable=False, server_default='10'))
    op.add_column('attestation_settings', 
        sa.Column('self_works_count', sa.Integer(), nullable=False, server_default='2'))
    op.add_column('attestation_settings', 
        sa.Column('colloquium_count', sa.Integer(), nullable=False, server_default='1'))
    
    # Коэффициент опоздания
    op.add_column('attestation_settings', 
        sa.Column('late_coef', sa.Float(), nullable=False, server_default='0.5'))
    
    # Убираем server_default после создания
    for col in ['grade_4_coef', 'grade_3_coef', 
                'labs_count_first', 'labs_count_second', 
                'self_works_count', 'colloquium_count', 'late_coef']:
        op.alter_column('attestation_settings', col, server_default=None)


def downgrade() -> None:
    # === УДАЛЕНИЕ НОВЫХ ПОЛЕЙ ===
    op.drop_column('attestation_settings', 'late_coef')
    op.drop_column('attestation_settings', 'colloquium_count')
    op.drop_column('attestation_settings', 'self_works_count')
    op.drop_column('attestation_settings', 'labs_count_second')
    op.drop_column('attestation_settings', 'labs_count_first')
    op.drop_column('attestation_settings', 'grade_3_coef')
    op.drop_column('attestation_settings', 'grade_4_coef')
    
    # === ПЕРЕИМЕНОВАНИЕ ОБРАТНО ===
    op.alter_column('attestation_settings', 'activity_reserve', 
                    new_column_name='activity_weight')
    
    # === ВОССТАНОВЛЕНИЕ УДАЛЁННЫХ ПОЛЕЙ ===
    op.add_column('attestation_settings', 
        sa.Column('participation_points', sa.Float(), nullable=False, server_default='0.5'))
    
    op.add_column('attestation_settings', 
        sa.Column('absent_points', sa.Float(), nullable=False, server_default='-0.1'))
    op.add_column('attestation_settings', 
        sa.Column('late_points', sa.Float(), nullable=False, server_default='0.5'))
    op.add_column('attestation_settings', 
        sa.Column('present_points', sa.Float(), nullable=False, server_default='1.0'))
    
    op.add_column('attestation_settings', 
        sa.Column('colloquium_grade_2_points', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('attestation_settings', 
        sa.Column('colloquium_grade_3_points', sa.Float(), nullable=False, server_default='5.0'))
    op.add_column('attestation_settings', 
        sa.Column('colloquium_grade_4_points', sa.Float(), nullable=False, server_default='10.0'))
    op.add_column('attestation_settings', 
        sa.Column('colloquium_grade_5_points', sa.Float(), nullable=False, server_default='15.0'))
    
    op.add_column('attestation_settings', 
        sa.Column('self_works_grade_2_points', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('attestation_settings', 
        sa.Column('self_works_grade_3_points', sa.Float(), nullable=False, server_default='4.0'))
    op.add_column('attestation_settings', 
        sa.Column('self_works_grade_4_points', sa.Float(), nullable=False, server_default='7.0'))
    op.add_column('attestation_settings', 
        sa.Column('self_works_grade_5_points', sa.Float(), nullable=False, server_default='10.0'))
    
    op.add_column('attestation_settings', 
        sa.Column('required_labs_count', sa.Integer(), nullable=False, server_default='5'))
    op.add_column('attestation_settings', 
        sa.Column('grade_2_points', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('attestation_settings', 
        sa.Column('grade_3_points', sa.Float(), nullable=False, server_default='4.0'))
    op.add_column('attestation_settings', 
        sa.Column('grade_4_points', sa.Float(), nullable=False, server_default='7.0'))
    op.add_column('attestation_settings', 
        sa.Column('grade_5_points', sa.Float(), nullable=False, server_default='10.0'))
