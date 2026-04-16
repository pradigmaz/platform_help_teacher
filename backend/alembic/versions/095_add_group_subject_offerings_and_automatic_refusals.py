"""Add group subject offerings and automatic pass refusals.

Revision ID: 095_add_group_subject_offerings_and_automatic_refusals
Revises: 094_add_automatic_enabled_to_lab_settings
Create Date: 2026-04-16
"""

from uuid import uuid4

import sqlalchemy as sa

from alembic import op

FINAL_CONTROL_TYPE_ENUM = sa.Enum(
    "exam",
    "credit",
    "differentiated_credit",
    name="finalcontroltype",
    native_enum=False,
    create_constraint=False,
)

revision = "095_add_group_subject_offerings_and_automatic_refusals"
down_revision = "094_add_automatic_enabled_to_lab_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create canonical group-subject offerings and refusal records."""
    bind = op.get_bind()
    op.create_table(
        "group_subject_offerings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("subject_id", sa.UUID(), nullable=False),
        sa.Column("semester", sa.String(length=10), nullable=False),
        sa.Column("final_control_type", FINAL_CONTROL_TYPE_ENUM, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "subject_id", "semester", name="uq_group_subject_offering_scope"),
    )
    op.create_index(op.f("ix_group_subject_offerings_group_id"), "group_subject_offerings", ["group_id"], unique=False)
    op.create_index(op.f("ix_group_subject_offerings_subject_id"), "group_subject_offerings", ["subject_id"], unique=False)
    op.create_index(op.f("ix_group_subject_offerings_semester"), "group_subject_offerings", ["semester"], unique=False)

    offerings_table = sa.table(
        "group_subject_offerings",
        sa.column("id", sa.UUID()),
        sa.column("group_id", sa.UUID()),
        sa.column("subject_id", sa.UUID()),
        sa.column("semester", sa.String(length=10)),
    )
    assignment_rows = list(
        bind.execute(
        sa.text(
            """
            SELECT DISTINCT group_id, subject_id, semester
            FROM teacher_subject_assignments
            WHERE group_id IS NOT NULL
              AND subject_id IS NOT NULL
              AND semester IS NOT NULL
            """
        )
    ).mappings()
    )
    assignment_offerings = [
            {
                "id": uuid4(),
                "group_id": row["group_id"],
                "subject_id": row["subject_id"],
                "semester": row["semester"],
            }
            for row in assignment_rows
        ]
    if assignment_offerings:
        op.bulk_insert(offerings_table, assignment_offerings)

    lesson_rows = list(
        bind.execute(
        sa.text(
            """
            SELECT DISTINCT
                lessons.group_id,
                lessons.subject_id,
                CASE
                    WHEN EXTRACT(MONTH FROM lessons.date) >= 9
                        THEN CONCAT(CAST(EXTRACT(YEAR FROM lessons.date) AS INTEGER), '-1')
                    WHEN EXTRACT(MONTH FROM lessons.date) <= 1
                        THEN CONCAT(CAST(EXTRACT(YEAR FROM lessons.date) AS INTEGER) - 1, '-1')
                    ELSE CONCAT(CAST(EXTRACT(YEAR FROM lessons.date) AS INTEGER) - 1, '-2')
                END AS semester
            FROM lessons
            WHERE lessons.group_id IS NOT NULL
              AND lessons.subject_id IS NOT NULL
            """
        )
    ).mappings()
    )
    existing_keys = {
        (row["group_id"], row["subject_id"], row["semester"])
        for row in bind.execute(
            sa.text("SELECT group_id, subject_id, semester FROM group_subject_offerings")
        ).mappings()
    }
    lesson_offerings = []
    for row in lesson_rows:
        key = (row["group_id"], row["subject_id"], row["semester"])
        if key in existing_keys:
            continue
        existing_keys.add(key)
        lesson_offerings.append(
            {
                "id": uuid4(),
                "group_id": row["group_id"],
                "subject_id": row["subject_id"],
                "semester": row["semester"],
            }
        )
    if lesson_offerings:
        op.bulk_insert(offerings_table, lesson_offerings)

    op.create_table(
        "automatic_pass_refusals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("offering_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("declined_by_admin_id", sa.UUID(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["declined_by_admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["offering_id"], ["group_subject_offerings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("offering_id", "student_id", name="uq_automatic_pass_refusal_scope"),
    )
    op.create_index(op.f("ix_automatic_pass_refusals_offering_id"), "automatic_pass_refusals", ["offering_id"], unique=False)
    op.create_index(op.f("ix_automatic_pass_refusals_student_id"), "automatic_pass_refusals", ["student_id"], unique=False)
    op.create_index(
        op.f("ix_automatic_pass_refusals_declined_by_admin_id"),
        "automatic_pass_refusals",
        ["declined_by_admin_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop canonical offering/refusal tables."""
    op.drop_index(op.f("ix_automatic_pass_refusals_declined_by_admin_id"), table_name="automatic_pass_refusals")
    op.drop_index(op.f("ix_automatic_pass_refusals_student_id"), table_name="automatic_pass_refusals")
    op.drop_index(op.f("ix_automatic_pass_refusals_offering_id"), table_name="automatic_pass_refusals")
    op.drop_table("automatic_pass_refusals")

    op.drop_index(op.f("ix_group_subject_offerings_semester"), table_name="group_subject_offerings")
    op.drop_index(op.f("ix_group_subject_offerings_subject_id"), table_name="group_subject_offerings")
    op.drop_index(op.f("ix_group_subject_offerings_group_id"), table_name="group_subject_offerings")
    op.drop_table("group_subject_offerings")
