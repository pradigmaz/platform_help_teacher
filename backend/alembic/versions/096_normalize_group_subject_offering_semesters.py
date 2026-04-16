"""Normalize spring semester offering keys to academic-year format.

Revision ID: 096_normalize_group_subject_offering_semesters
Revises: 095_add_group_subject_offerings_and_automatic_refusals
Create Date: 2026-04-16
"""

import sqlalchemy as sa

from alembic import op

revision = "096_normalize_group_subject_offering_semesters"
down_revision = "095_add_group_subject_offerings_and_automatic_refusals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix offering semester keys created from spring lessons as calendar-year-2."""
    op.execute(
        """
        WITH lesson_semesters AS (
            SELECT DISTINCT
                lessons.group_id,
                lessons.subject_id,
                CONCAT(CAST(EXTRACT(YEAR FROM lessons.date) AS INTEGER), '-2') AS wrong_semester,
                CONCAT(CAST(EXTRACT(YEAR FROM lessons.date) AS INTEGER) - 1, '-2') AS correct_semester
            FROM lessons
            WHERE lessons.group_id IS NOT NULL
              AND lessons.subject_id IS NOT NULL
              AND EXTRACT(MONTH FROM lessons.date) BETWEEN 2 AND 8
        )
        DELETE FROM group_subject_offerings AS g
        USING lesson_semesters AS l
        WHERE g.group_id = l.group_id
          AND g.subject_id = l.subject_id
          AND g.semester = l.wrong_semester
          AND EXISTS (
              SELECT 1
              FROM group_subject_offerings AS existing
              WHERE existing.group_id = g.group_id
                AND existing.subject_id = g.subject_id
                AND existing.semester = l.correct_semester
          )
        """
    )
    op.execute(
        """
        WITH lesson_semesters AS (
            SELECT DISTINCT
                lessons.group_id,
                lessons.subject_id,
                CONCAT(CAST(EXTRACT(YEAR FROM lessons.date) AS INTEGER), '-2') AS wrong_semester,
                CONCAT(CAST(EXTRACT(YEAR FROM lessons.date) AS INTEGER) - 1, '-2') AS correct_semester
            FROM lessons
            WHERE lessons.group_id IS NOT NULL
              AND lessons.subject_id IS NOT NULL
              AND EXTRACT(MONTH FROM lessons.date) BETWEEN 2 AND 8
        )
        UPDATE group_subject_offerings AS g
        SET semester = l.correct_semester,
            updated_at = NOW()
        FROM lesson_semesters AS l
        WHERE g.group_id = l.group_id
          AND g.subject_id = l.subject_id
          AND g.semester = l.wrong_semester
        """
    )


def downgrade() -> None:
    """Best-effort rollback for semester normalization."""
    op.execute(
        """
        WITH lesson_semesters AS (
            SELECT DISTINCT
                lessons.group_id,
                lessons.subject_id,
                CONCAT(CAST(EXTRACT(YEAR FROM lessons.date) AS INTEGER), '-2') AS wrong_semester,
                CONCAT(CAST(EXTRACT(YEAR FROM lessons.date) AS INTEGER) - 1, '-2') AS correct_semester
            FROM lessons
            WHERE lessons.group_id IS NOT NULL
              AND lessons.subject_id IS NOT NULL
              AND EXTRACT(MONTH FROM lessons.date) BETWEEN 2 AND 8
        )
        UPDATE group_subject_offerings AS g
        SET semester = l.wrong_semester,
            updated_at = NOW()
        FROM lesson_semesters AS l
        WHERE g.group_id = l.group_id
          AND g.subject_id = l.subject_id
          AND g.semester = l.correct_semester
          AND NOT EXISTS (
              SELECT 1
              FROM group_subject_offerings AS existing
              WHERE existing.group_id = g.group_id
                AND existing.subject_id = g.subject_id
                AND existing.semester = l.wrong_semester
          )
        """
    )
