"""Refactor attestation settings - remove dead code, add configurable grade points

Revision ID: 064_refactor_attestation
Revises: 063_fix_audit_timezone
Create Date: 2026-01-09

Changes:
- Remove: components_config (JSONB), bonus_per_extra_lab, soft_deadline_penalty, 
          hard_deadline_penalty, excused_points
- Rename: soft_deadline_days -> late_threshold_days
- Add: grade_X_points (configurable points per grade), late_max_grade, very_late_max_grade
- Add: self_works_* fields (self-study works component)
- Add: colloquium_* fields (colloquium component)
- Add: grade_2_points for completeness
"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = '064_refactor_attestation'
down_revision: Union[str, None] = '063_fix_audit_timezone'
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # === УДАЛЕНИЕ МЁРТВОГО КОДА ===
    op.drop_column('attestation_settings', 'components_config')
    op.drop_column('attestation_settings', 'bonus_per_extra_lab')
    op.drop_column('attestation_settings', 'soft_deadline_penalty')
    op.drop_column('attestation_settings', 'hard_deadline_penalty')
    op.drop_column('attestation_settings', 'excused_points')
    
    # === ПЕРЕИМЕНОВАНИЕ ===
    op.alter_column('attestation_settings', 'soft_deadline_days', 
                    new_column_name='late_threshold_days')
    
    # === БАЛЛЫ ЗА ОЦЕНКИ ЛАБОРАТОРНЫХ (настраиваемые) ===
    op.add_column('attestation_settings', 
        sa.Column('grade_5_points', sa.Float(), nullable=False, server_default='10.0'))
    op.add_column('attestation_settings', 
        sa.Column('grade_4_points', sa.Float(), nullable=False, server_default='7.0'))
    op.add_column('attestation_settings', 
        sa.Column('grade_3_points', sa.Float(), nullable=False, server_default='4.0'))
    op.add_column('attestation_settings', 
        sa.Column('grade_2_points', sa.Float(), nullable=False, server_default='0.0'))
    
    # === ОГРАНИЧЕНИЕ ОЦЕНКИ ПРИ ПРОСРОЧКЕ ===
    op.add_column('attestation_settings', 
        sa.Column('late_max_grade', sa.Integer(), nullable=False, server_default='4'))
    op.add_column('attestation_settings', 
        sa.Column('very_late_max_grade', sa.Integer(), nullable=False, server_default='3'))
    
    # === САМОСТОЯТЕЛЬНЫЕ РАБОТЫ ===
    op.add_column('attestation_settings', 
        sa.Column('self_works_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('attestation_settings', 
        sa.Column('self_works_weight', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('attestation_settings', 
        sa.Column('self_works_grade_5_points', sa.Float(), nullable=False, server_default='10.0'))
    op.add_column('attestation_settings', 
        sa.Column('self_works_grade_4_points', sa.Float(), nullable=False, server_default='7.0'))
    op.add_column('attestation_settings', 
        sa.Column('self_works_grade_3_points', sa.Float(), nullable=False, server_default='4.0'))
    op.add_column('attestation_settings', 
        sa.Column('self_works_grade_2_points', sa.Float(), nullable=False, server_default='0.0'))
    
    # === КОЛЛОКВИУМ ===
    op.add_column('attestation_settings', 
        sa.Column('colloquium_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('attestation_settings', 
        sa.Column('colloquium_weight', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('attestation_settings', 
        sa.Column('colloquium_grade_5_points', sa.Float(), nullable=False, server_default='15.0'))
    op.add_column('attestation_settings', 
        sa.Column('colloquium_grade_4_points', sa.Float(), nullable=False, server_default='10.0'))
    op.add_column('attestation_settings', 
        sa.Column('colloquium_grade_3_points', sa.Float(), nullable=False, server_default='5.0'))
    op.add_column('attestation_settings', 
        sa.Column('colloquium_grade_2_points', sa.Float(), nullable=False, server_default='0.0'))
    
    # Убираем server_default после создания
    for col in ['grade_5_points', 'grade_4_points', 'grade_3_points', 'grade_2_points',
                'late_max_grade', 'very_late_max_grade',
                'self_works_enabled', 'self_works_weight', 
                'self_works_grade_5_points', 'self_works_grade_4_points', 
                'self_works_grade_3_points', 'self_works_grade_2_points',
                'colloquium_enabled', 'colloquium_weight',
                'colloquium_grade_5_points', 'colloquium_grade_4_points',
                'colloquium_grade_3_points', 'colloquium_grade_2_points']:
        op.alter_column('attestation_settings', col, server_default=None)


def downgrade() -> None:
    # === УДАЛЕНИЕ НОВЫХ ПОЛЕЙ ===
    op.drop_column('attestation_settings', 'colloquium_grade_2_points')
    op.drop_column('attestation_settings', 'colloquium_grade_3_points')
    op.drop_column('attestation_settings', 'colloquium_grade_4_points')
    op.drop_column('attestation_settings', 'colloquium_grade_5_points')
    op.drop_column('attestation_settings', 'colloquium_weight')
    op.drop_column('attestation_settings', 'colloquium_enabled')
    
    op.drop_column('attestation_settings', 'self_works_grade_2_points')
    op.drop_column('attestation_settings', 'self_works_grade_3_points')
    op.drop_column('attestation_settings', 'self_works_grade_4_points')
    op.drop_column('attestation_settings', 'self_works_grade_5_points')
    op.drop_column('attestation_settings', 'self_works_weight')
    op.drop_column('attestation_settings', 'self_works_enabled')
    
    op.drop_column('attestation_settings', 'very_late_max_grade')
    op.drop_column('attestation_settings', 'late_max_grade')
    
    op.drop_column('attestation_settings', 'grade_2_points')
    op.drop_column('attestation_settings', 'grade_3_points')
    op.drop_column('attestation_settings', 'grade_4_points')
    op.drop_column('attestation_settings', 'grade_5_points')
    
    # === ПЕРЕИМЕНОВАНИЕ ОБРАТНО ===
    op.alter_column('attestation_settings', 'late_threshold_days', 
                    new_column_name='soft_deadline_days')
    
    # === ВОССТАНОВЛЕНИЕ УДАЛЁННЫХ ПОЛЕЙ ===
    op.add_column('attestation_settings', 
        sa.Column('excused_points', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('attestation_settings', 
        sa.Column('hard_deadline_penalty', sa.Float(), nullable=False, server_default='0.5'))
    op.add_column('attestation_settings', 
        sa.Column('soft_deadline_penalty', sa.Float(), nullable=False, server_default='0.7'))
    op.add_column('attestation_settings', 
        sa.Column('bonus_per_extra_lab', sa.Float(), nullable=False, server_default='0.4'))
    op.add_column('attestation_settings', 
        sa.Column('components_config', JSONB(), nullable=True))
