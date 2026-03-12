"""Cleanup duplicate lesson_grades for the same student/subject/work_number.

Revision ID: 084_cleanup_duplicate_lesson_grades
Revises: 083_labs_subject_number_uq
Create Date: 2026-03-11
"""

from alembic import op

revision = "084_cleanup_duplicate_lesson_grades"
down_revision = "083_labs_subject_number_uq"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Keep one canonical row per (student_id, subject_id, work_number):
    # highest grade first, then latest row, then highest UUID as a stable tie-breaker.
    op.execute(
        """
        WITH ranked_duplicates AS (
            SELECT
                lg.id,
                ROW_NUMBER() OVER (
                    PARTITION BY lg.student_id, l.subject_id, lg.work_number
                    ORDER BY lg.grade DESC, lg.updated_at DESC, lg.created_at DESC, lg.id DESC
                ) AS row_num
            FROM lesson_grades lg
            JOIN lessons l ON l.id = lg.lesson_id
            WHERE lg.work_number IS NOT NULL
              AND l.subject_id IS NOT NULL
        )
        DELETE FROM lesson_grades lg
        USING ranked_duplicates rd
        WHERE lg.id = rd.id
          AND rd.row_num > 1
        """
    )


def downgrade() -> None:
    # Irreversible data cleanup migration.
    pass
