"""Add student_audit_log table

Revision ID: 049
Revises: 048
Create Date: 2026-01-08

Полный аудит действий студентов.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = '049'
down_revision = '048'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаём таблицу аудита
    op.create_table(
        'student_audit_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        
        # Идентификация пользователя
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('session_id', sa.String(64), nullable=True),
        
        # Действие
        sa.Column('action_type', sa.String(20), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=True),
        
        # HTTP контекст
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('path', sa.String(500), nullable=False),
        sa.Column('query_params', JSONB, nullable=True),
        sa.Column('request_body', JSONB, nullable=True),
        sa.Column('response_status', sa.SmallInteger(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        
        # Клиент
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('ip_forwarded', sa.String(200), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        
        # Fingerprint и дополнительные данные
        sa.Column('fingerprint', JSONB, nullable=True),
        sa.Column('extra_data', JSONB, nullable=True),
        
        # Timestamp
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Индексы для быстрого поиска
    op.create_index('idx_student_audit_user_id', 'student_audit_log', ['user_id'])
    op.create_index('idx_student_audit_created_at', 'student_audit_log', ['created_at'])
    op.create_index('idx_student_audit_action_type', 'student_audit_log', ['action_type'])
    op.create_index('idx_student_audit_ip', 'student_audit_log', ['ip_address'])
    op.create_index('idx_student_audit_session', 'student_audit_log', ['session_id'])
    op.create_index('idx_student_audit_entity', 'student_audit_log', ['entity_type', 'entity_id'])
    op.create_index('idx_student_audit_user_time', 'student_audit_log', ['user_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_student_audit_user_time', table_name='student_audit_log')
    op.drop_index('idx_student_audit_entity', table_name='student_audit_log')
    op.drop_index('idx_student_audit_session', table_name='student_audit_log')
    op.drop_index('idx_student_audit_ip', table_name='student_audit_log')
    op.drop_index('idx_student_audit_action_type', table_name='student_audit_log')
    op.drop_index('idx_student_audit_created_at', table_name='student_audit_log')
    op.drop_index('idx_student_audit_user_id', table_name='student_audit_log')
    op.drop_table('student_audit_log')
