"""varchar to text with check constraints

Revision ID: 014_varchar_to_text
Revises: 013_add_activity_table
Create Date: 2024-12-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '014_varchar_to_text'
down_revision: Union[str, None] = '013_add_activity_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users: VARCHAR -> TEXT + CHECK
    op.alter_column('users', 'full_name', type_=sa.Text(), existing_type=sa.String(200))
    op.alter_column('users', 'username', type_=sa.Text(), existing_type=sa.String(100))
    op.alter_column('users', 'invite_code', type_=sa.Text(), existing_type=sa.String(8))
    
    op.create_check_constraint('ck_users_full_name_len', 'users', 'length(full_name) <= 200')
    op.create_check_constraint('ck_users_username_len', 'users', 'length(username) <= 100')
    op.create_check_constraint('ck_users_invite_code_len', 'users', 'length(invite_code) <= 8')
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    
    # Groups: VARCHAR -> TEXT + CHECK
    op.alter_column('groups', 'code', type_=sa.Text(), existing_type=sa.String(20))
    op.alter_column('groups', 'name', type_=sa.Text(), existing_type=sa.String(100))
    
    op.create_check_constraint('ck_groups_code_len', 'groups', 'length(code) <= 20')
    op.create_check_constraint('ck_groups_name_len', 'groups', 'length(name) <= 100')
    
    # Labs: VARCHAR -> TEXT + CHECK
    op.alter_column('labs', 'title', type_=sa.Text(), existing_type=sa.String(200))
    op.alter_column('labs', 's3_key', type_=sa.Text(), existing_type=sa.String(500))
    
    op.create_check_constraint('ck_labs_title_len', 'labs', 'length(title) <= 200')
    op.create_check_constraint('ck_labs_s3_key_len', 'labs', 'length(s3_key) <= 500')
    
    # Lectures: VARCHAR -> TEXT + CHECK
    op.alter_column('lectures', 'title', type_=sa.Text(), existing_type=sa.String(300))
    
    op.create_check_constraint('ck_lectures_title_len', 'lectures', 'length(title) <= 300')
    
    # Activities: VARCHAR -> TEXT + CHECK + index
    op.alter_column('activities', 'description', type_=sa.Text(), existing_type=sa.String(500))
    
    op.create_check_constraint('ck_activities_description_len', 'activities', 'length(description) <= 500')
    op.create_index('ix_activities_created_at', 'activities', ['created_at'])


def downgrade() -> None:
    # Activities
    op.drop_index('ix_activities_created_at', 'activities')
    op.drop_constraint('ck_activities_description_len', 'activities', type_='check')
    op.alter_column('activities', 'description', type_=sa.String(500), existing_type=sa.Text())
    
    # Lectures
    op.drop_constraint('ck_lectures_title_len', 'lectures', type_='check')
    op.alter_column('lectures', 'title', type_=sa.String(300), existing_type=sa.Text())
    
    # Labs
    op.drop_constraint('ck_labs_s3_key_len', 'labs', type_='check')
    op.drop_constraint('ck_labs_title_len', 'labs', type_='check')
    op.alter_column('labs', 's3_key', type_=sa.String(500), existing_type=sa.Text())
    op.alter_column('labs', 'title', type_=sa.String(200), existing_type=sa.Text())
    
    # Groups
    op.drop_constraint('ck_groups_name_len', 'groups', type_='check')
    op.drop_constraint('ck_groups_code_len', 'groups', type_='check')
    op.alter_column('groups', 'name', type_=sa.String(100), existing_type=sa.Text())
    op.alter_column('groups', 'code', type_=sa.String(20), existing_type=sa.Text())
    
    # Users
    op.drop_index('ix_users_created_at', 'users')
    op.drop_constraint('ck_users_invite_code_len', 'users', type_='check')
    op.drop_constraint('ck_users_username_len', 'users', type_='check')
    op.drop_constraint('ck_users_full_name_len', 'users', type_='check')
    op.alter_column('users', 'invite_code', type_=sa.String(8), existing_type=sa.Text())
    op.alter_column('users', 'username', type_=sa.String(100), existing_type=sa.Text())
    op.alter_column('users', 'full_name', type_=sa.String(200), existing_type=sa.Text())
