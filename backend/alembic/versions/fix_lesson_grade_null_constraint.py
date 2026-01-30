"""Add partial unique index for lesson_grades with NULL work_number.

Fixes race condition where multiple grades with work_number=NULL
could be created for the same (lesson_id, student_id) because
PostgreSQL treats NULL != NULL in unique constraints.

Revision ID: 078_fix_lesson_grade_null_constraint
Revises: 077_add_uploaded_fields_to_attachments
Create Date: 2026-01-30
"""
from alembic import op

# revision identifiers
revision = '078_fix_lesson_grade_null_constraint'
down_revision = '077_add_uploaded_fields_to_attachments'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Remove duplicates (keep the one with highest grade)
    # This is necessary because unique index will fail if duplicates exist
    op.execute("""
        DELETE FROM lesson_grades lg1
        USING lesson_grades lg2
        WHERE lg1.lesson_id = lg2.lesson_id
          AND lg1.student_id = lg2.student_id
          AND lg1.work_number IS NULL
          AND lg2.work_number IS NULL
          AND lg1.id != lg2.id
          AND (lg1.grade < lg2.grade OR (lg1.grade = lg2.grade AND lg1.created_at < lg2.created_at))
    """)
    
    # Step 2: Create partial unique index for records where work_number IS NULL
    # This prevents duplicates like (lesson_id, student_id, NULL)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_lesson_grade_student_lesson_null_work 
        ON lesson_grades (lesson_id, student_id) 
        WHERE work_number IS NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_lesson_grade_student_lesson_null_work")
