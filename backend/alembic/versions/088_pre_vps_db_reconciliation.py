"""Reconcile duplicate indexes and missing audit/admin read indexes.

Revision ID: 088_pre_vps_db_reconciliation
Revises: 087_admin_read_path_indexes
Create Date: 2026-03-28
"""

import sqlalchemy as sa

from alembic import op

revision = "088_pre_vps_db_reconciliation"
down_revision = "087_admin_read_path_indexes"
branch_labels = None
depends_on = None


def _create_admin_read_indexes() -> None:
    op.create_index(
        "idx_lessons_group_subject_date_active",
        "lessons",
        ["group_id", "subject_id", "date"],
        unique=False,
        postgresql_where=sa.text("is_cancelled = false"),
        if_not_exists=True,
    )
    op.create_index(
        "idx_attendance_group_lesson",
        "attendance",
        ["group_id", "lesson_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "idx_users_group_role_active",
        "users",
        ["group_id", "role", "is_active"],
        unique=False,
        if_not_exists=True,
    )


def _create_missing_audit_indexes() -> None:
    op.create_index(
        "idx_audit_fingerprint_gin",
        "student_audit_log",
        ["fingerprint"],
        postgresql_using="gin",
        postgresql_ops={"fingerprint": "jsonb_path_ops"},
        if_not_exists=True,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_audit_fingerprint_user
        ON student_audit_log (user_id)
        WHERE fingerprint IS NOT NULL AND user_id IS NOT NULL
        """
    )
    op.create_index(
        "idx_audit_role_time",
        "student_audit_log",
        ["actor_role", "created_at"],
        unique=False,
        if_not_exists=True,
    )


def _drop_duplicate_indexes() -> None:
    op.drop_index("ix_devices_id", table_name="devices", if_exists=True)
    op.drop_index("ix_devices_user_fingerprint", table_name="devices", if_exists=True)
    op.drop_index("ix_notification_settings_user_id", table_name="notification_settings", if_exists=True)
    op.drop_index("ix_subjects_name", table_name="subjects", if_exists=True)


def upgrade() -> None:
    _create_admin_read_indexes()
    _create_missing_audit_indexes()
    _drop_duplicate_indexes()


def downgrade() -> None:
    op.create_index("ix_subjects_name", "subjects", ["name"], unique=False, if_not_exists=True)
    op.create_index(
        "ix_notification_settings_user_id",
        "notification_settings",
        ["user_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_devices_user_fingerprint",
        "devices",
        ["user_id", "fingerprint_hash"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index("ix_devices_id", "devices", ["id"], unique=False, if_not_exists=True)

    op.drop_index("idx_audit_role_time", table_name="student_audit_log", if_exists=True)
    op.drop_index("idx_audit_fingerprint_user", table_name="student_audit_log", if_exists=True)
    op.drop_index("idx_audit_fingerprint_gin", table_name="student_audit_log", if_exists=True)

    op.drop_index("idx_users_group_role_active", table_name="users", if_exists=True)
    op.drop_index("idx_attendance_group_lesson", table_name="attendance", if_exists=True)
    op.drop_index("idx_lessons_group_subject_date_active", table_name="lessons", if_exists=True)
