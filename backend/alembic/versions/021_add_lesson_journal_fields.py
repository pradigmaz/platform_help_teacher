"""Add journal fields to lessons and create lesson_grades table

Revision ID: 021_add_lesson_journal_fields
Revises: 020_add_subject_tables
Create Date: 2026-01-03
"""
from typing import Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = '021_add_lesson_journal_fields'
down_revision: Union[str, None] = '020_add_subject_tables'
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # 1. Add subject_id to lessons
    op.add_column('lessons', sa.Column('subject_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_lessons_subject',
        'lessons', 'subjects',
        ['subject_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_lessons_subject_id', 'lessons', ['subject_id'])

    # 2. Add work_number to lessons (номер лабы/практики: 1, 2, 3...)
    op.add_column('lessons', sa.Column('work_number', sa.Integer, nullable=True))

    # 3. Add lecture_work_type to lessons (quiz/selfwork для контрольных на лекциях)
    op.add_column('lessons', sa.Column('lecture_work_type', sa.String(20), nullable=True))

    # 4. Create lesson_grades table
    op.create_table(
        'lesson_grades',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lesson_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('lessons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('work_number', sa.Integer, nullable=True),  # какую работу сдаёт (может != lesson.work_number)
        sa.Column('grade', sa.Integer, nullable=False),  # 2-5
        sa.Column('comment', sa.String(500), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_lesson_grades_lesson_id', 'lesson_grades', ['lesson_id'])
    op.create_index('ix_lesson_grades_student_id', 'lesson_grades', ['student_id'])
    op.create_unique_constraint(
        'uq_lesson_grade_student_lesson_work',
        'lesson_grades',
        ['lesson_id', 'student_id', 'work_number']
    )


def downgrade() -> None:
    # Drop lesson_grades
    op.drop_constraint('uq_lesson_grade_student_lesson_work', 'lesson_grades', type_='unique')
    op.drop_index('ix_lesson_grades_student_id', 'lesson_grades')
    op.drop_index('ix_lesson_grades_lesson_id', 'lesson_grades')
    op.drop_table('lesson_grades')

    # Drop lesson columns
    op.drop_column('lessons', 'lecture_work_type')
    op.drop_column('lessons', 'work_number')
    op.drop_index('ix_lessons_subject_id', 'lessons')
    op.drop_constraint('fk_lessons_subject', 'lessons', type_='foreignkey')
    op.drop_column('lessons', 'subject_id')
