"""Fix device table datetime columns to use timezone

Revision ID: 082_fix_device_datetime_tz
Revises: 081_fix_lecture_html_entities
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa

revision = "082_fix_device_datetime_tz"
down_revision = "081_fix_lecture_html_entities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("devices", "first_seen", type_=sa.DateTime(timezone=True))
    op.alter_column("devices", "last_seen", type_=sa.DateTime(timezone=True))
    op.alter_column("devices", "confirmed_at", type_=sa.DateTime(timezone=True))
    op.alter_column("devices", "created_at", type_=sa.DateTime(timezone=True))
    op.alter_column("devices", "updated_at", type_=sa.DateTime(timezone=True))


def downgrade() -> None:
    op.alter_column("devices", "first_seen", type_=sa.DateTime())
    op.alter_column("devices", "last_seen", type_=sa.DateTime())
    op.alter_column("devices", "confirmed_at", type_=sa.DateTime())
    op.alter_column("devices", "created_at", type_=sa.DateTime())
    op.alter_column("devices", "updated_at", type_=sa.DateTime())
