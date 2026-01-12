"""Add feedback table

Revision ID: 069_add_feedback_table
Revises: 068_add_lesson_visibility_index
Create Date: 2026-01-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '069_add_feedback_table'
down_revision = '068_add_lesson_visibility_index'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    feedback_type = postgresql.ENUM('bug', 'suggestion', name='feedbacktype', create_type=False)
    feedback_type.create(op.get_bind(), checkfirst=True)
    
    feedback_status = postgresql.ENUM('new', 'in_progress', 'resolved', 'closed', name='feedbackstatus', create_type=False)
    feedback_status.create(op.get_bind(), checkfirst=True)
    
    op.create_table(
        'feedback',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('type', sa.Enum('bug', 'suggestion', name='feedbacktype'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('new', 'in_progress', 'resolved', 'closed', name='feedbackstatus'), nullable=False, server_default='new'),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('admin_response', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_feedback_user_id', 'feedback', ['user_id'])
    op.create_index('ix_feedback_status', 'feedback', ['status'])
    op.create_index('ix_feedback_created_at', 'feedback', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_feedback_created_at', table_name='feedback')
    op.drop_index('ix_feedback_status', table_name='feedback')
    op.drop_index('ix_feedback_user_id', table_name='feedback')
    op.drop_table('feedback')
    
    op.execute('DROP TYPE IF EXISTS feedbackstatus')
    op.execute('DROP TYPE IF EXISTS feedbacktype')
