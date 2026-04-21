"""Add shared exam question banks.

Revision ID: 100_add_exam_question_banks
Revises: 099_add_exam_prep_questions_to_group_subject_offerings
Create Date: 2026-04-21
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "100_add_exam_question_banks"
down_revision = "099_add_exam_prep_questions_to_group_subject_offerings"
branch_labels = None
depends_on = None


bank_table = sa.table(
    "exam_question_banks",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("subject_id", postgresql.UUID(as_uuid=True)),
    sa.column("semester", sa.String(length=10)),
    sa.column("questions", postgresql.JSONB(astext_type=sa.Text())),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)

offering_table = sa.table(
    "group_subject_offerings",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("subject_id", postgresql.UUID(as_uuid=True)),
    sa.column("semester", sa.String(length=10)),
    sa.column("exam_prep_questions", postgresql.JSONB(astext_type=sa.Text())),
    sa.column("exam_question_bank_id", postgresql.UUID(as_uuid=True)),
)


def upgrade() -> None:
    op.create_table(
        "exam_question_banks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("semester", sa.String(length=10), nullable=False),
        sa.Column("questions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exam_question_banks_semester"), "exam_question_banks", ["semester"], unique=False)
    op.create_index(op.f("ix_exam_question_banks_subject_id"), "exam_question_banks", ["subject_id"], unique=False)

    op.add_column(
        "group_subject_offerings",
        sa.Column("exam_question_bank_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        op.f("ix_group_subject_offerings_exam_question_bank_id"),
        "group_subject_offerings",
        ["exam_question_bank_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_group_subject_offerings_exam_question_bank_id",
        "group_subject_offerings",
        "exam_question_banks",
        ["exam_question_bank_id"],
        ["id"],
        ondelete="SET NULL",
    )

    connection = op.get_bind()
    rows = connection.execute(
        sa.select(
            offering_table.c.id,
            offering_table.c.subject_id,
            offering_table.c.semester,
            offering_table.c.exam_prep_questions,
        )
    ).mappings()
    now = datetime.now(timezone.utc)
    for row in rows:
        questions = row["exam_prep_questions"] or []
        if not questions:
            continue
        bank_id = uuid4()
        connection.execute(
            sa.insert(bank_table).values(
                id=bank_id,
                subject_id=row["subject_id"],
                semester=row["semester"],
                questions=questions,
                created_at=now,
                updated_at=now,
            )
        )
        connection.execute(
            sa.update(offering_table)
            .where(offering_table.c.id == row["id"])
            .values(exam_question_bank_id=bank_id)
        )


def downgrade() -> None:
    connection = op.get_bind()
    rows = connection.execute(
        sa.select(
            offering_table.c.id,
            offering_table.c.exam_question_bank_id,
            bank_table.c.questions,
        ).select_from(
            offering_table.outerjoin(bank_table, offering_table.c.exam_question_bank_id == bank_table.c.id)
        )
    ).mappings()
    for row in rows:
        if row["exam_question_bank_id"] is None:
            continue
        connection.execute(
            sa.update(offering_table)
            .where(offering_table.c.id == row["id"])
            .values(exam_prep_questions=row["questions"] or [])
        )

    op.drop_constraint("fk_group_subject_offerings_exam_question_bank_id", "group_subject_offerings", type_="foreignkey")
    op.drop_index(op.f("ix_group_subject_offerings_exam_question_bank_id"), table_name="group_subject_offerings")
    op.drop_column("group_subject_offerings", "exam_question_bank_id")

    op.drop_index(op.f("ix_exam_question_banks_subject_id"), table_name="exam_question_banks")
    op.drop_index(op.f("ix_exam_question_banks_semester"), table_name="exam_question_banks")
    op.drop_table("exam_question_banks")
