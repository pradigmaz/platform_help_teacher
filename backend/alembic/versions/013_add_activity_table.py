"""add activity table

Revision ID: 013_add_activity_table
Revises: 012_add_optimization_indexes
Create Date: 2024-12-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '013_add_activity_table'
down_revision = '012_add_optimization_indexes'
branch_labels = None
depends_on = None


def upgrade():
    # Create activity table
    op.create_table('activities',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('points', sa.Float(), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('attestation_type', sa.Enum('FIRST', 'SECOND', name='attestationtype'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('batch_id', sa.UUID(), nullable=True),
        sa.Column('created_by_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activities_batch_id'), 'activities', ['batch_id'], unique=False)
    op.create_index(op.f('ix_activities_is_active'), 'activities', ['is_active'], unique=False)
    op.create_index(op.f('ix_activities_student_id'), 'activities', ['student_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_activities_student_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_is_active'), table_name='activities')
    op.drop_index(op.f('ix_activities_batch_id'), table_name='activities')
    op.drop_table('activities')

