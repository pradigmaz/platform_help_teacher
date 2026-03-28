"""Shared planning/apply logic for deterministic legacy journal cleanup."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text

NULL_DUPLICATES_SQL = """
SELECT
    lg.id::text AS grade_id,
    lg.lesson_id::text AS lesson_id,
    lg.student_id::text AS student_id,
    lg.grade,
    TO_CHAR(l.date, 'YYYY-MM-DD') AS lesson_date,
    l.lesson_number,
    COALESCE((
        SELECT string_agg(other.id::text, ',' ORDER BY other.id)
        FROM lesson_grades other
        WHERE other.lesson_id = lg.lesson_id
          AND other.student_id = lg.student_id
          AND other.grade = lg.grade
          AND other.work_number IS NOT NULL
    ), '') AS twin_grade_ids
FROM lesson_grades lg
JOIN lessons l ON l.id = lg.lesson_id
WHERE l.lesson_type IN ('LAB', 'PRACTICE')
  AND lg.grade IS NOT NULL
  AND lg.work_number IS NULL
  AND EXISTS (
      SELECT 1
      FROM lesson_grades twin
      WHERE twin.lesson_id = lg.lesson_id
        AND twin.student_id = lg.student_id
        AND twin.grade = lg.grade
        AND twin.work_number IS NOT NULL
  )
ORDER BY l.date, l.lesson_number, lg.lesson_id, lg.student_id, lg.id
"""

CONFLICT_ROWS_SQL = """
WITH conflict_cells AS (
    SELECT
        l.subject_id,
        l.work_number AS lesson_work_number,
        l.date,
        l.lesson_number,
        lg.lesson_id,
        lg.student_id
    FROM lesson_grades lg
    JOIN lessons l ON l.id = lg.lesson_id
    WHERE lg.work_number IS NOT NULL
    GROUP BY l.subject_id, l.work_number, l.date, l.lesson_number, lg.lesson_id, lg.student_id
    HAVING COUNT(DISTINCT lg.work_number) > 1
)
SELECT
    cc.lesson_id::text AS lesson_id,
    cc.student_id::text AS student_id,
    lg.id::text AS grade_id,
    lg.work_number,
    lg.grade,
    COALESCE(cc.lesson_work_number, -1) AS lesson_work_number,
    TO_CHAR(cc.date, 'YYYY-MM-DD') AS lesson_date,
    cc.lesson_number,
    EXISTS (
        SELECT 1
        FROM submissions s
        JOIN labs lab ON lab.id = s.lab_id
        WHERE s.user_id = cc.student_id
          AND s.deleted_at IS NULL
          AND s.status = 'ACCEPTED'
          AND lab.subject_id = cc.subject_id
          AND lab.number = lg.work_number
    ) AS has_submission
FROM conflict_cells cc
JOIN lesson_grades lg
  ON lg.lesson_id = cc.lesson_id
 AND lg.student_id = cc.student_id
 AND lg.work_number IS NOT NULL
ORDER BY cc.date, cc.lesson_number, cc.lesson_id, cc.student_id, lg.work_number, lg.id
"""


async def fetch_all(session, sql: str, **params: Any) -> list[dict[str, Any]]:
    result = await session.execute(text(sql), params)
    return [dict(row) for row in result.mappings().all()]


async def fetch_scalar(session, sql: str, **params: Any) -> Any:
    result = await session.execute(text(sql), params)
    return result.scalar()


async def has_submission_lesson_id_column(session) -> bool:
    return bool(
        await fetch_scalar(
            session,
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'submissions'
                  AND column_name = 'lesson_id'
            )
            """,
        )
    )


async def load_legacy_submissions(session, has_lesson_id: bool) -> list[dict[str, Any]]:
    lesson_filter = "AND s.lesson_id IS NULL" if has_lesson_id else ""
    sql = f"""
    SELECT
        s.id::text AS submission_id,
        s.user_id::text AS user_id,
        lab.subject_id::text AS subject_id,
        lab.number AS lab_number,
        TO_CHAR(s.lesson_date, 'YYYY-MM-DD') AS lesson_date,
        s.lesson_number
    FROM submissions s
    JOIN labs lab ON lab.id = s.lab_id
    WHERE (s.lesson_date IS NOT NULL OR s.lesson_number IS NOT NULL)
      {lesson_filter}
    ORDER BY s.created_at, s.id
    """
    return await fetch_all(session, sql)


async def find_explicit_lesson(session, submission: dict[str, Any]) -> str | None:
    if not submission["lesson_date"] or submission["lesson_number"] is None:
        return None
    rows = await fetch_all(
        session,
        """
        SELECT l.id::text AS lesson_id
        FROM lessons l
        WHERE l.subject_id = CAST(:subject_id AS uuid)
          AND TO_CHAR(l.date, 'YYYY-MM-DD') = :lesson_date
          AND l.lesson_number = :lesson_number
          AND l.lesson_type IN ('LAB', 'PRACTICE')
        ORDER BY l.id
        """,
        subject_id=submission["subject_id"],
        lesson_date=submission["lesson_date"],
        lesson_number=submission["lesson_number"],
    )
    return rows[0]["lesson_id"] if len(rows) == 1 else None


async def find_grade_matched_lesson(session, submission: dict[str, Any]) -> str | None:
    rows = await fetch_all(
        session,
        """
        SELECT DISTINCT lg.lesson_id::text AS lesson_id
        FROM lesson_grades lg
        JOIN lessons l ON l.id = lg.lesson_id
        WHERE lg.student_id = CAST(:user_id AS uuid)
          AND l.subject_id = CAST(:subject_id AS uuid)
          AND lg.work_number = :lab_number
        """,
        user_id=submission["user_id"],
        subject_id=submission["subject_id"],
        lab_number=submission["lab_number"],
    )
    return rows[0]["lesson_id"] if len(rows) == 1 else None


async def find_attendance_matched_lesson(session, submission: dict[str, Any]) -> str | None:
    if not submission["lesson_date"]:
        return None
    rows = await fetch_all(
        session,
        """
        SELECT DISTINCT a.lesson_id::text AS lesson_id
        FROM attendance a
        JOIN lessons l ON l.id = a.lesson_id
        WHERE a.student_id = CAST(:user_id AS uuid)
          AND TO_CHAR(a.date, 'YYYY-MM-DD') = :lesson_date
          AND a.status IN ('PRESENT', 'LATE', 'EXCUSED')
          AND l.subject_id = CAST(:subject_id AS uuid)
          AND l.lesson_type IN ('LAB', 'PRACTICE')
        """,
        user_id=submission["user_id"],
        lesson_date=submission["lesson_date"],
        subject_id=submission["subject_id"],
    )
    return rows[0]["lesson_id"] if len(rows) == 1 else None


async def build_plan(session) -> dict[str, Any]:
    null_duplicates = await fetch_all(session, NULL_DUPLICATES_SQL)
    conflict_rows = await fetch_all(session, CONFLICT_ROWS_SQL)
    has_lesson_id = await has_submission_lesson_id_column(session)
    legacy_submissions = await load_legacy_submissions(session, has_lesson_id)

    grouped_conflicts: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in conflict_rows:
        grouped_conflicts[(row["lesson_id"], row["student_id"])].append(row)

    auto_conflict_deletes: list[dict[str, Any]] = []
    manual_conflicts: list[dict[str, Any]] = []
    for (lesson_id, student_id), rows in grouped_conflicts.items():
        with_submission = [row for row in rows if row["has_submission"]]
        if len(with_submission) == 1:
            keep_id = with_submission[0]["grade_id"]
            auto_conflict_deletes.extend([row for row in rows if row["grade_id"] != keep_id])
            continue
        manual_conflicts.append({"lesson_id": lesson_id, "student_id": student_id, "rows": rows})

    submission_updates: list[dict[str, Any]] = []
    unresolved_submissions: list[dict[str, Any]] = []
    for submission in legacy_submissions:
        sources = [
            ("date_number", await find_explicit_lesson(session, submission)),
            ("grade_match", await find_grade_matched_lesson(session, submission)),
            ("attendance_same_date", await find_attendance_matched_lesson(session, submission)),
        ]
        resolved = next(((source, lesson_id) for source, lesson_id in sources if lesson_id), None)
        if resolved:
            source, lesson_id = resolved
            submission_updates.append({**submission, "lesson_id": lesson_id, "source": source})
            continue
        unresolved_submissions.append(submission)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "has_submission_lesson_id_column": has_lesson_id,
        "null_duplicate_deletes": null_duplicates,
        "conflict_deletes": auto_conflict_deletes,
        "manual_conflicts": manual_conflicts,
        "submission_updates": submission_updates,
        "unresolved_submissions": unresolved_submissions,
    }


def print_plan(plan: dict[str, Any]) -> None:
    print("=" * 72)
    print("LEGACY CLEANUP PLAN")
    print("=" * 72)
    print(f"submissions.lesson_id column exists: {plan['has_submission_lesson_id_column']}")
    print(f"Null duplicate grade deletes: {len(plan['null_duplicate_deletes'])}")
    print(f"Submission backfills: {len(plan['submission_updates'])}")
    print(f"Conflict grade deletes: {len(plan['conflict_deletes'])}")
    print(f"Manual conflict cells: {len(plan['manual_conflicts'])}")
    print(f"Unresolved submissions: {len(plan['unresolved_submissions'])}")
    if plan["manual_conflicts"]:
        print("\nManual conflict cells:")
        for conflict in plan["manual_conflicts"]:
            variants = ", ".join(
                f"grade_id={row['grade_id']} work={row['work_number']} "
                f"grade={row['grade']} has_submission={row['has_submission']}"
                for row in conflict["rows"]
            )
            print(f"  - lesson={conflict['lesson_id']} student={conflict['student_id']} -> {variants}")
    if plan["unresolved_submissions"]:
        print("\nUnresolved submissions:")
        for row in plan["unresolved_submissions"]:
            print(
                f"  - submission={row['submission_id']} user={row['user_id']} "
                f"lab={row['lab_number']} date={row['lesson_date']} lesson={row['lesson_number']}"
            )


async def apply_plan(session, plan: dict[str, Any]) -> None:
    if not plan["has_submission_lesson_id_column"]:
        raise RuntimeError("submissions.lesson_id column is missing. Apply alembic revision 085 first.")

    async with session.begin():
        await session.execute(text("SET LOCAL lock_timeout = '2s'"))
        await session.execute(text("SET LOCAL statement_timeout = '15s'"))

        for row in plan["submission_updates"]:
            await session.execute(
                text(
                    "UPDATE submissions "
                    "SET lesson_id = CAST(:lesson_id AS uuid) "
                    "WHERE id = CAST(:submission_id AS uuid) AND lesson_id IS NULL"
                ),
                {"submission_id": row["submission_id"], "lesson_id": row["lesson_id"]},
            )

        delete_ids = [row["grade_id"] for row in plan["null_duplicate_deletes"] + plan["conflict_deletes"]]
        for grade_id in delete_ids:
            await session.execute(
                text("DELETE FROM lesson_grades WHERE id = CAST(:grade_id AS uuid)"),
                {"grade_id": grade_id},
            )
