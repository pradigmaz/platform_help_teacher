"""Add devices table for user device binding.

Revision ID: 080_add_devices_table
Revises: 079_add_max_labs_override_to_lessons
Create Date: 2026-02-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "080_add_devices_table"
down_revision = "079_add_max_labs_override_to_lessons"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create devices table
    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fingerprint_hash", sa.String(length=64), nullable=False),
        sa.Column("device_info", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("first_seen", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_seen", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_trusted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "fingerprint_hash", name="uq_devices_user_fingerprint"),
    )
    
    # Create indexes
    op.create_index("ix_devices_id", "devices", ["id"], unique=False)
    op.create_index("ix_devices_user_id", "devices", ["user_id"], unique=False)
    op.create_index("ix_devices_fingerprint_hash", "devices", ["fingerprint_hash"], unique=False)
    op.create_index("ix_devices_last_seen", "devices", ["last_seen"], unique=False)
    op.create_index("ix_devices_user_fingerprint", "devices", ["user_id", "fingerprint_hash"], unique=False)
    op.create_index("ix_devices_user_trusted", "devices", ["user_id", "is_trusted"], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_devices_user_trusted", table_name="devices")
    op.drop_index("ix_devices_user_fingerprint", table_name="devices")
    op.drop_index("ix_devices_last_seen", table_name="devices")
    op.drop_index("ix_devices_fingerprint_hash", table_name="devices")
    op.drop_index("ix_devices_user_id", table_name="devices")
    op.drop_index("ix_devices_id", table_name="devices")
    
    # Drop table
    op.drop_table("devices")
