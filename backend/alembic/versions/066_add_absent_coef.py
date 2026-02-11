"""Add absent_coef to attestation_settings

Revision ID: 066_add_absent_coef
Revises: 065_autobalance_attestation
Create Date: 2026-01-10
"""

from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "066_add_absent_coef"
down_revision: Union[str, None] = "065_autobalance_attestation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("attestation_settings", sa.Column("absent_coef", sa.Float(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("attestation_settings", "absent_coef")
