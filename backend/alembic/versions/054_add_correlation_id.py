"""Add correlation_id to student_audit_log

Revision ID: 054
Revises: 053
Create Date: 2026-01-08

Добавляет поле correlation_id для связи цепочек действий.
"""
from alembic import op
import sqlalchemy as sa


revision = '054'
down_revision = '053'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем колонку в партиционированную таблицу
    op.add_column(
        'student_audit_log',
        sa.Column('correlation_id', sa.String(64), nullable=True)
    )
    
    # Индекс для поиска по correlation_id
    op.create_index(
        'idx_audit_correlation_id',
        'student_audit_log',
        ['correlation_id']
    )


def downgrade() -> None:
    op.drop_index('idx_audit_correlation_id', table_name='student_audit_log')
    op.drop_column('student_audit_log', 'correlation_id')
