"""Audit table optimizations: GIN index + partitioning prep

Revision ID: 052
Revises: 051_add_actor_role_to_audit
Create Date: 2026-01-08

Добавляет:
1. GIN индекс на fingerprint для быстрого поиска по JSONB
2. Подготовка к партиционированию (комментарии)
"""
from alembic import op
import sqlalchemy as sa


revision = '052'
down_revision = '051_add_actor_role'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. GIN индекс на fingerprint для быстрого поиска по JSONB
    # Позволяет эффективно искать по любым ключам внутри fingerprint
    op.create_index(
        'idx_audit_fingerprint_gin',
        'student_audit_log',
        ['fingerprint'],
        postgresql_using='gin',
        postgresql_ops={'fingerprint': 'jsonb_path_ops'},
        if_not_exists=True
    )
    
    # 2. Частичный индекс для suspicion queries (fingerprint + user_id)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_fingerprint_user 
        ON student_audit_log (user_id) 
        WHERE fingerprint IS NOT NULL AND user_id IS NOT NULL
    """)
    
    # 3. Индекс для быстрой фильтрации по actor_role + created_at
    op.create_index(
        'idx_audit_role_time',
        'student_audit_log',
        ['actor_role', 'created_at'],
        if_not_exists=True
    )


def downgrade() -> None:
    op.drop_index('idx_audit_role_time', table_name='student_audit_log', if_exists=True)
    op.drop_index('idx_audit_fingerprint_user', table_name='student_audit_log', if_exists=True)
    op.drop_index('idx_audit_fingerprint_gin', table_name='student_audit_log', if_exists=True)
