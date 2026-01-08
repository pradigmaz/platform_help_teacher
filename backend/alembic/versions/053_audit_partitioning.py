"""Partition student_audit_log by month

Revision ID: 053
Revises: 052
Create Date: 2026-01-08

Партиционирование по RANGE(created_at) позволяет:
- Быстрое удаление старых данных (DROP PARTITION)
- Эффективные запросы по временным диапазонам
- Параллельное сканирование партиций
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta


revision = '053'
down_revision = '052'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Создаём новую partitioned таблицу
    op.execute("""
        CREATE TABLE student_audit_log_partitioned (
            id UUID NOT NULL,
            user_id UUID,
            session_id VARCHAR(64),
            actor_role VARCHAR(20) NOT NULL DEFAULT 'anonymous',
            action_type VARCHAR(20) NOT NULL,
            entity_type VARCHAR(50),
            entity_id UUID,
            method VARCHAR(10) NOT NULL,
            path VARCHAR(500) NOT NULL,
            query_params JSONB,
            request_body JSONB,
            response_status SMALLINT,
            duration_ms INTEGER,
            ip_address VARCHAR(45) NOT NULL,
            ip_forwarded VARCHAR(200),
            user_agent VARCHAR(512),
            fingerprint JSONB,
            extra_data JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id, created_at)
        ) PARTITION BY RANGE (created_at)
    """)
    
    # 2. Создаём партиции на 12 месяцев вперёд
    now = datetime.utcnow()
    for i in range(12):
        month_start = datetime(now.year, now.month, 1) + timedelta(days=32 * i)
        month_start = datetime(month_start.year, month_start.month, 1)
        next_month = month_start + timedelta(days=32)
        next_month = datetime(next_month.year, next_month.month, 1)
        
        partition_name = f"student_audit_log_y{month_start.year}m{month_start.month:02d}"
        
        op.execute(f"""
            CREATE TABLE IF NOT EXISTS {partition_name}
            PARTITION OF student_audit_log_partitioned
            FOR VALUES FROM ('{month_start.strftime('%Y-%m-%d')}') 
            TO ('{next_month.strftime('%Y-%m-%d')}')
        """)
    
    # 3. Создаём default партицию для данных вне диапазона
    op.execute("""
        CREATE TABLE IF NOT EXISTS student_audit_log_default
        PARTITION OF student_audit_log_partitioned DEFAULT
    """)
    
    # 4. Копируем данные из старой таблицы (явный порядок колонок)
    op.execute("""
        INSERT INTO student_audit_log_partitioned 
        (id, user_id, session_id, actor_role, action_type, entity_type, entity_id,
         method, path, query_params, request_body, response_status, duration_ms,
         ip_address, ip_forwarded, user_agent, fingerprint, extra_data, created_at)
        SELECT id, user_id, session_id, actor_role, action_type, entity_type, entity_id,
               method, path, query_params, request_body, response_status, duration_ms,
               ip_address, ip_forwarded, user_agent, fingerprint, extra_data, created_at
        FROM student_audit_log
    """)
    
    # 5. Переименовываем таблицы (atomic swap)
    op.execute("ALTER TABLE student_audit_log RENAME TO student_audit_log_old")
    op.execute("ALTER TABLE student_audit_log_partitioned RENAME TO student_audit_log")
    
    # 6. Пересоздаём индексы на новой таблице
    op.create_index('idx_student_audit_user_id_new', 'student_audit_log', ['user_id'])
    op.create_index('idx_student_audit_created_at_new', 'student_audit_log', ['created_at'])
    op.create_index('idx_student_audit_action_type_new', 'student_audit_log', ['action_type'])
    op.create_index('idx_student_audit_ip_new', 'student_audit_log', ['ip_address'])
    op.create_index('idx_student_audit_session_new', 'student_audit_log', ['session_id'])
    op.create_index('idx_audit_entity_new', 'student_audit_log', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_user_time_new', 'student_audit_log', ['user_id', 'created_at'])
    op.create_index('idx_student_audit_actor_role_new', 'student_audit_log', ['actor_role'])
    op.create_index(
        'idx_audit_fingerprint_gin_new', 
        'student_audit_log', 
        ['fingerprint'],
        postgresql_using='gin',
        postgresql_ops={'fingerprint': 'jsonb_path_ops'}
    )
    
    # 7. Функция для автоматического создания партиций (вызывать через cron/celery)
    op.execute(
        "CREATE OR REPLACE FUNCTION create_audit_partition_if_needed() "
        "RETURNS void AS $func$ "
        "DECLARE "
        "    partition_date DATE; "
        "    partition_name TEXT; "
        "    start_date DATE; "
        "    end_date DATE; "
        "BEGIN "
        "    partition_date := DATE_TRUNC('month', NOW() + INTERVAL '1 month'); "
        "    partition_name := 'student_audit_log_y' || "
        "                     EXTRACT(YEAR FROM partition_date)::TEXT || "
        "                     'm' || LPAD(EXTRACT(MONTH FROM partition_date)::TEXT, 2, '0'); "
        "    start_date := partition_date; "
        "    end_date := partition_date + INTERVAL '1 month'; "
        "    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = partition_name) THEN "
        "        EXECUTE format('CREATE TABLE %I PARTITION OF student_audit_log FOR VALUES FROM (%L) TO (%L)', "
        "                       partition_name, start_date, end_date); "
        "    END IF; "
        "END; "
        "$func$ LANGUAGE plpgsql;"
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS create_audit_partition_if_needed()")
    op.execute("ALTER TABLE student_audit_log RENAME TO student_audit_log_partitioned")
    op.execute("ALTER TABLE student_audit_log_old RENAME TO student_audit_log")
    op.execute("DROP TABLE student_audit_log_partitioned CASCADE")
