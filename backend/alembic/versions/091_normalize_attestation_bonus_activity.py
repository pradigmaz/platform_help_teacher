"""Normalize attestation base weights for bonus activity.

Revision ID: 091_normalize_attestation_bonus_activity
Revises: 090_add_announcement_delivery_state
Create Date: 2026-04-16
"""

from alembic import op

revision = "091_normalize_attestation_bonus_activity"
down_revision = "090_add_announcement_delivery_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Preserve base weight ratios while moving activity outside the 100% base."""
    op.execute(
        """
        WITH base AS (
            SELECT
                id,
                labs_weight,
                attendance_weight,
                self_works_weight,
                colloquium_weight,
                self_works_enabled,
                colloquium_enabled,
                (
                    labs_weight
                    + attendance_weight
                    + CASE WHEN self_works_enabled THEN self_works_weight ELSE 0 END
                    + CASE WHEN colloquium_enabled THEN colloquium_weight ELSE 0 END
                ) AS base_total
            FROM attestation_settings
        )
        UPDATE attestation_settings AS settings
        SET
            labs_weight = CASE
                WHEN base.base_total <= 0 THEN 70.0
                ELSE base.labs_weight * 100.0 / base.base_total
            END,
            attendance_weight = CASE
                WHEN base.base_total <= 0 THEN 30.0
                ELSE base.attendance_weight * 100.0 / base.base_total
            END,
            self_works_weight = CASE
                WHEN base.base_total <= 0 THEN 0.0
                WHEN base.self_works_enabled THEN base.self_works_weight * 100.0 / base.base_total
                ELSE base.self_works_weight
            END,
            colloquium_weight = CASE
                WHEN base.base_total <= 0 THEN 0.0
                WHEN base.colloquium_enabled THEN base.colloquium_weight * 100.0 / base.base_total
                ELSE base.colloquium_weight
            END
        FROM base
        WHERE settings.id = base.id
          AND (base.base_total <= 0 OR ABS(base.base_total - 100.0) > 0.01)
        """
    )


def downgrade() -> None:
    """Best-effort rollback to the legacy shape where activity occupied base weight."""
    op.execute(
        """
        WITH base AS (
            SELECT
                id,
                labs_weight,
                attendance_weight,
                self_works_weight,
                colloquium_weight,
                self_works_enabled,
                colloquium_enabled,
                GREATEST(100.0 - activity_reserve, 0.0) AS target_total,
                (
                    labs_weight
                    + attendance_weight
                    + CASE WHEN self_works_enabled THEN self_works_weight ELSE 0 END
                    + CASE WHEN colloquium_enabled THEN colloquium_weight ELSE 0 END
                ) AS base_total
            FROM attestation_settings
        )
        UPDATE attestation_settings AS settings
        SET
            labs_weight = CASE
                WHEN base.base_total <= 0 THEN base.target_total * 0.7
                ELSE base.labs_weight * base.target_total / base.base_total
            END,
            attendance_weight = CASE
                WHEN base.base_total <= 0 THEN base.target_total * 0.3
                ELSE base.attendance_weight * base.target_total / base.base_total
            END,
            self_works_weight = CASE
                WHEN base.base_total <= 0 THEN 0.0
                WHEN base.self_works_enabled THEN base.self_works_weight * base.target_total / base.base_total
                ELSE base.self_works_weight
            END,
            colloquium_weight = CASE
                WHEN base.base_total <= 0 THEN 0.0
                WHEN base.colloquium_enabled THEN base.colloquium_weight * base.target_total / base.base_total
                ELSE base.colloquium_weight
            END
        FROM base
        WHERE settings.id = base.id
          AND (base.base_total <= 0 OR ABS(base.base_total - base.target_total) > 0.01)
        """
    )
