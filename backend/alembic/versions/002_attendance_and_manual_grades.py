"""attendance_and_manual_grades

Revision ID: 002
Revises: 001_initial
Create Date: 2025-12-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '3545f90960b4'  # ID initial миграции
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 0. Создаем функцию для updated_at триггера
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # 1. Создаем ENUM для посещаемости
    op.execute("CREATE TYPE attendance_status_enum AS ENUM ('PRESENT', 'ABSENT', 'LATE', 'EXCUSED')")

    # 2. Создаем таблицу attendance
    op.create_table(
        'attendance',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('status', postgresql.ENUM('PRESENT', 'ABSENT', 'LATE', 'EXCUSED', name='attendance_status_enum', create_type=False), server_default='ABSENT', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'date', name='uq_attendance_student_date')
    )
    op.create_index('idx_attendance_group_date', 'attendance', ['group_id', 'date'], unique=False)

    # 3. Обновляем таблицу submissions (поддержка ручных оценок)
    # Делаем s3_key необязательным
    op.alter_column('submissions', 's3_key', existing_type=sa.VARCHAR(length=500), nullable=True)
    
    # Добавляем флаг is_manual
    op.add_column('submissions', sa.Column('is_manual', sa.Boolean(), server_default='false', nullable=False))
    
    # Добавляем Constraint: Либо есть файл, либо это ручная оценка
    op.create_check_constraint(
        'check_file_required_if_not_manual',
        'submissions',
        '(is_manual IS TRUE) OR (s3_key IS NOT NULL)'
    )

    # 4. Триггер для updated_at в attendance
    op.execute("""
        CREATE TRIGGER update_attendance_updated_at 
        BEFORE UPDATE ON attendance 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS update_attendance_updated_at ON attendance")
    op.drop_check_constraint('check_file_required_if_not_manual', 'submissions')
    op.drop_column('submissions', 'is_manual')
    # Возвращаем s3_key как NOT NULL (может упасть, если есть NULL данные)
    op.execute("UPDATE submissions SET s3_key = 'deleted' WHERE s3_key IS NULL") 
    op.alter_column('submissions', 's3_key', existing_type=sa.VARCHAR(length=500), nullable=False)
    
    op.drop_index('idx_attendance_group_date', table_name='attendance')
    op.drop_table('attendance')
    op.execute("DROP TYPE attendance_status_enum")