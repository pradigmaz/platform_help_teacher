"""Create attendance table if not exists

Revision ID: 022_create_attendance_table
Revises: 021_add_lesson_journal_fields
Create Date: 2026-01-03
"""
from typing import Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op
from sqlalchemy import inspect

revision: str = '022_create_attendance_table'
down_revision: Union[str, None] = '021_add_lesson_journal_fields'
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    
    if 'attendance' not in tables:
        # Create ENUM type if not exists
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE attendance_status_enum AS ENUM ('PRESENT', 'ABSENT', 'LATE', 'EXCUSED');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        
        # Create attendance table
        op.create_table(
            'attendance',
            sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
            sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False),
            sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('status', postgresql.ENUM('PRESENT', 'ABSENT', 'LATE', 'EXCUSED', name='attendance_status_enum', create_type=False), server_default='ABSENT', nullable=False),
            sa.Column('lesson_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lessons.id', ondelete='SET NULL'), nullable=True),
            sa.Column('lesson_type', sa.String(20), nullable=True),
            sa.Column('lesson_number', sa.Integer(), nullable=True),
            sa.Column('subgroup', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        
        op.create_index('idx_attendance_group_date', 'attendance', ['group_id', 'date'])
        op.create_index('idx_attendance_lesson', 'attendance', ['lesson_id'])
        op.create_unique_constraint('uq_attendance_student_date_lesson', 'attendance', ['student_id', 'date', 'lesson_number'])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    
    if 'attendance' in tables:
        op.drop_constraint('uq_attendance_student_date_lesson', 'attendance', type_='unique')
        op.drop_index('idx_attendance_lesson', table_name='attendance')
        op.drop_index('idx_attendance_group_date', table_name='attendance')
        op.drop_table('attendance')
