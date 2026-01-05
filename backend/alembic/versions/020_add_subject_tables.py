"""Add subject and teacher_subject_assignments tables

Revision ID: 020_add_subject_tables
Revises: 019_add_onboarding_completed
Create Date: 2026-01-03
"""
from typing import Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = '020_add_subject_tables'
down_revision: Union[str, None] = '019_add_onboarding_completed'
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # 1. Create subjects table
    op.create_table(
        'subjects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_subjects_name_lower', 'subjects', ['name'])

    # 2. Create teacher_subject_assignments table
    op.create_table(
        'teacher_subject_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('groups.id', ondelete='CASCADE'), nullable=True),
        sa.Column('semester', sa.String(10), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_tsa_teacher_id', 'teacher_subject_assignments', ['teacher_id'])
    op.create_index('ix_tsa_subject_id', 'teacher_subject_assignments', ['subject_id'])
    op.create_index('ix_tsa_group_id', 'teacher_subject_assignments', ['group_id'])
    op.create_index('idx_tsa_teacher_semester', 'teacher_subject_assignments', ['teacher_id', 'semester'])
    op.create_unique_constraint(
        'uq_teacher_subject_group_semester',
        'teacher_subject_assignments',
        ['teacher_id', 'subject_id', 'group_id', 'semester']
    )

    # 3. Add subject_id to schedule_items (optional FK, keep subject string for compatibility)
    op.add_column('schedule_items', sa.Column('subject_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_schedule_items_subject',
        'schedule_items', 'subjects',
        ['subject_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_schedule_items_subject_id', 'schedule_items', ['subject_id'])

    # 4. Add subject_id to works (optional)
    op.add_column('works', sa.Column('subject_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_works_subject',
        'works', 'subjects',
        ['subject_id'], ['id'],
        ondelete='SET NULL'
    )

    # 5. Add group_id to works (optional)
    op.add_column('works', sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_works_group',
        'works', 'groups',
        ['group_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Works
    op.drop_constraint('fk_works_group', 'works', type_='foreignkey')
    op.drop_column('works', 'group_id')
    op.drop_constraint('fk_works_subject', 'works', type_='foreignkey')
    op.drop_column('works', 'subject_id')

    # Schedule items
    op.drop_index('ix_schedule_items_subject_id', 'schedule_items')
    op.drop_constraint('fk_schedule_items_subject', 'schedule_items', type_='foreignkey')
    op.drop_column('schedule_items', 'subject_id')

    # Teacher subject assignments
    op.drop_constraint('uq_teacher_subject_group_semester', 'teacher_subject_assignments', type_='unique')
    op.drop_index('idx_tsa_teacher_semester', 'teacher_subject_assignments')
    op.drop_index('ix_tsa_group_id', 'teacher_subject_assignments')
    op.drop_index('ix_tsa_subject_id', 'teacher_subject_assignments')
    op.drop_index('ix_tsa_teacher_id', 'teacher_subject_assignments')
    op.drop_table('teacher_subject_assignments')

    # Subjects
    op.drop_index('idx_subjects_name_lower', 'subjects')
    op.drop_table('subjects')
