"""Add lab_deadline_extensions table

Revision ID: 076_add_deadline_extensions
Revises: 075_link_admin_to_subjects
Create Date: 2026-01-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '076_deadline_extensions'
down_revision = '075_link_admin_to_subjects'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'lab_deadline_extensions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('lab_id', UUID(as_uuid=True), sa.ForeignKey('labs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('group_id', UUID(as_uuid=True), sa.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bonus_lessons', sa.Integer(), nullable=False, default=1),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, server_default='true'),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint('lab_id', 'group_id', name='uq_lab_deadline_extension_lab_group'),
    )
    
    op.create_index('ix_lab_deadline_extensions_lab_id', 'lab_deadline_extensions', ['lab_id'])
    op.create_index('ix_lab_deadline_extensions_group_id', 'lab_deadline_extensions', ['group_id'])
    op.create_index('ix_lab_deadline_extensions_is_active', 'lab_deadline_extensions', ['is_active'])


def downgrade() -> None:
    op.drop_index('ix_lab_deadline_extensions_is_active')
    op.drop_index('ix_lab_deadline_extensions_group_id')
    op.drop_index('ix_lab_deadline_extensions_lab_id')
    op.drop_table('lab_deadline_extensions')
