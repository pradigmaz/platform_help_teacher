"""add schedule_items and lessons tables, update attendance

Revision ID: 017_add_schedule_and_lessons
Revises: 016_add_components_config
Create Date: 2024-12-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '017_add_schedule_and_lessons'
down_revision: Union[str, None] = '016_add_components_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Таблица schedule_items (расписание)
    op.create_table(
        'schedule_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('day_of_week', sa.String(20), nullable=False),  # monday, tuesday, etc.
        sa.Column('lesson_number', sa.Integer(), nullable=False),  # 1-8
        sa.Column('lesson_type', sa.String(20), nullable=False),  # lecture, practice, lab
        sa.Column('subject', sa.String(255), nullable=True),
        sa.Column('room', sa.String(50), nullable=True),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('week_parity', sa.String(10), nullable=True),  # odd, even, null
        sa.Column('subgroup', sa.Integer(), nullable=True),  # 1, 2, null
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('idx_schedule_group_day', 'schedule_items', ['group_id', 'day_of_week'])
    
    # 2. Таблица lessons (конкретные занятия)
    op.create_table(
        'lessons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('schedule_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schedule_items.id', ondelete='SET NULL'), nullable=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('lesson_number', sa.Integer(), nullable=False),
        sa.Column('lesson_type', sa.String(20), nullable=False),
        sa.Column('topic', sa.String(500), nullable=True),
        sa.Column('work_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('works.id', ondelete='SET NULL'), nullable=True),
        sa.Column('subgroup', sa.Integer(), nullable=True),
        sa.Column('is_cancelled', sa.Boolean(), default=False, nullable=False),
        sa.Column('cancellation_reason', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('idx_lessons_group_date', 'lessons', ['group_id', 'date'])
    
    # 3. Обновление attendance - добавляем новые поля (если таблица существует)
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    
    if 'attendance' in tables:
        op.add_column('attendance', sa.Column('lesson_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.add_column('attendance', sa.Column('lesson_type', sa.String(20), nullable=True))
        op.add_column('attendance', sa.Column('lesson_number', sa.Integer(), nullable=True))
        op.add_column('attendance', sa.Column('subgroup', sa.Integer(), nullable=True))
        
        # FK constraint отдельно
        op.create_foreign_key('fk_attendance_lesson', 'attendance', 'lessons', ['lesson_id'], ['id'], ondelete='SET NULL')
        op.create_index('idx_attendance_lesson', 'attendance', ['lesson_id'])
        
        # Удаляем старый unique constraint и создаём новый
        try:
            op.drop_constraint('uq_attendance_student_date', 'attendance', type_='unique')
        except Exception:
            pass  # constraint может не существовать
        op.create_unique_constraint('uq_attendance_student_date_lesson', 'attendance', ['student_id', 'date', 'lesson_number'])


def downgrade() -> None:
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    
    # Откат attendance (если таблица существует)
    if 'attendance' in tables:
        try:
            op.drop_constraint('uq_attendance_student_date_lesson', 'attendance', type_='unique')
        except Exception:
            pass
        try:
            op.create_unique_constraint('uq_attendance_student_date', 'attendance', ['student_id', 'date'])
        except Exception:
            pass
        
        try:
            op.drop_index('idx_attendance_lesson', table_name='attendance')
        except Exception:
            pass
        try:
            op.drop_constraint('fk_attendance_lesson', 'attendance', type_='foreignkey')
        except Exception:
            pass
        
        for col in ['subgroup', 'lesson_number', 'lesson_type', 'lesson_id']:
            try:
                op.drop_column('attendance', col)
            except Exception:
                pass
    
    # Удаление таблиц
    op.drop_index('idx_lessons_group_date', table_name='lessons')
    op.drop_table('lessons')
    
    op.drop_index('idx_schedule_group_day', table_name='schedule_items')
    op.drop_table('schedule_items')
