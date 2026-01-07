"""Add student_transfers table

Revision ID: 036_student_transfers
Revises: 035_group_has_subgroups
Create Date: 2026-01-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = '036_student_transfers'
down_revision: Union[str, None] = '035_group_has_subgroups'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'student_transfers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('from_group_id', UUID(as_uuid=True), sa.ForeignKey('groups.id', ondelete='SET NULL'), nullable=True),
        sa.Column('from_subgroup', sa.Integer(), nullable=True),
        sa.Column('to_group_id', UUID(as_uuid=True), sa.ForeignKey('groups.id', ondelete='SET NULL'), nullable=True),
        sa.Column('to_subgroup', sa.Integer(), nullable=True),
        sa.Column('transfer_date', sa.Date(), nullable=False),
        sa.Column('attestation_type', sa.String(10), nullable=False),
        sa.Column('attendance_data', JSONB(), nullable=False, server_default='{}'),
        sa.Column('lab_grades_data', JSONB(), nullable=False, server_default='[]'),
        sa.Column('activity_points', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('ix_student_transfers_transfer_date', 'student_transfers', ['transfer_date'])


def downgrade() -> None:
    op.drop_index('ix_student_transfers_transfer_date', table_name='student_transfers')
    op.drop_table('student_transfers')
