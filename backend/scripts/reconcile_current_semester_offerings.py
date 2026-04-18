"""Report and safe backfill for current-semester offering scope."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import date
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
for candidate in (str(ROOT), "/app"):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from sqlalchemy import or_, select

from app.crud.crud_group_subject_offering import ensure_group_subject_offering_for_date, get_current_semester_key
from app.db.session import AsyncSessionLocal
from app.models.lesson import Lesson
from app.models.schedule import ScheduleItem
from app.services.schedule_offering_resolution import resolve_schedule_offering_scope


def semester_bounds(semester_key: str) -> tuple[date, date]:
    year_str, semester_str = semester_key.split("-")
    year = int(year_str)
    if semester_str == "1":
        return date(year, 9, 1), date(year + 1, 1, 31)
    return date(year, 2, 1), date(year, 8, 31)

async def build_report(session, semester_key: str) -> dict:
    start_date, end_date = semester_bounds(semester_key)
    lessons = await _load_lessons(session, start_date, end_date)
    schedule_items = await _load_schedule_items(session, start_date, end_date)
    report = {
        "semester": semester_key,
        "bounds": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "lessons_missing_offering": [],
        "schedule_items_missing_offering": [],
        "lessons_mismatch": [],
        "schedule_items_mismatch": [],
        "missing_offerings": [],
    }
    missing_offerings: set[tuple[str, str, str]] = set()

    for lesson in lessons:
        await _inspect_row(session, report, missing_offerings, lesson, lesson.date, "lesson")
    for item in schedule_items:
        await _inspect_row(session, report, missing_offerings, item, item.start_date, "schedule_item")

    report["missing_offerings"] = [
        {"group_id": group_id, "subject_id": subject_id, "reference_date": reference_date}
        for group_id, subject_id, reference_date in sorted(missing_offerings)
    ]
    return report

async def _inspect_row(session, report: dict, missing_offerings: set, row, reference_date: date, kind: str) -> None:
    scope = await resolve_schedule_offering_scope(
        session,
        group_id=row.group_id,
        reference_date=reference_date,
        subject_id=row.subject_id,
        require_existing=False,
    )
    row_payload = {"id": str(row.id), "group_id": str(row.group_id), "subject_id": str(row.subject_id)}
    if scope.offering_id is None:
        missing_offerings.add((str(row.group_id), str(row.subject_id), reference_date.isoformat()))
        return
    if row.offering_id is None:
        report[f"{kind}s_missing_offering"].append({**row_payload, "expected_offering_id": str(scope.offering_id)})
        return
    if row.offering_id != scope.offering_id:
        report[f"{kind}s_mismatch"].append(
            {
                **row_payload,
                "offering_id": str(row.offering_id),
                "expected_offering_id": str(scope.offering_id),
            }
        )

async def _load_lessons(session, start_date: date, end_date: date) -> list[Lesson]:
    result = await session.execute(
        select(Lesson).where(
            Lesson.subject_id.isnot(None),
            Lesson.date >= start_date,
            Lesson.date <= end_date,
        )
    )
    return list(result.scalars().all())

async def _load_schedule_items(session, start_date: date, end_date: date) -> list[ScheduleItem]:
    result = await session.execute(
        select(ScheduleItem).where(
            ScheduleItem.subject_id.isnot(None),
            ScheduleItem.start_date <= end_date,
            or_(ScheduleItem.end_date.is_(None), ScheduleItem.end_date >= start_date),
        )
    )
    return list(result.scalars().all())

async def apply_backfill(session, semester_key: str) -> dict:
    report = await build_report(session, semester_key)
    for item in report["missing_offerings"]:
        await ensure_group_subject_offering_for_date(
            session,
            group_id=UUID(item["group_id"]),
            subject_id=UUID(item["subject_id"]),
            lesson_date=date.fromisoformat(item["reference_date"]),
        )

    for model, key in (
        (Lesson, "lessons_missing_offering"),
        (ScheduleItem, "schedule_items_missing_offering"),
    ):
        for row_info in report[key]:
            row = await session.get(model, UUID(row_info["id"]))
            if row is not None and row.offering_id is None:
                row.offering_id = UUID(row_info["expected_offering_id"])
    await session.commit()
    return await build_report(session, semester_key)

async def run(apply: bool, backup_confirmed: bool) -> int:
    if apply and not backup_confirmed:
        raise SystemExit("--backup-confirmed is required with --apply")
    async with AsyncSessionLocal() as session:
        semester_key = await get_current_semester_key(session)
        report = await build_report(session, semester_key)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if not apply:
            await session.rollback()
            return 0
        post_report = await apply_backfill(session, semester_key)
        print(json.dumps({"post_apply": post_report}, ensure_ascii=False, indent=2))
        return 0

def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile current-semester lesson/schedule offering scope.")
    parser.add_argument("--apply", action="store_true", help="Create missing offerings and fill missing offering_id.")
    parser.add_argument("--backup-confirmed", action="store_true", help="Required with --apply after a fresh backup.")
    args = parser.parse_args()
    return asyncio.run(run(args.apply, args.backup_confirmed))

if __name__ == "__main__":
    raise SystemExit(main())
