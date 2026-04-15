"""CLI for importing lab grades from teacher date notes."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict
from datetime import date
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
for candidate in (str(ROOT), "/app"):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models import User, UserRole
from app.services.lab_grade_import.parser import parse_grade_notes
from app.services.lab_grade_import.planner import DEFAULT_START_DATE, LabGradeImportPlanner
from app.services.lab_grade_import.types import ImportPlan

REPO_ROOT = ROOT.parent
DEFAULT_INPUT = REPO_ROOT / "даты" / "Текстовый файл.md"
TEACHER_ROLES = {UserRole.ADMIN, UserRole.TEACHER}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import lab grades from teacher notes.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Markdown notes file.")
    parser.add_argument("--apply", action="store_true", help="Write the planned grades to the database.")
    parser.add_argument(
        "--parse-only", action="store_true", help="Only parse notes without connecting to the database."
    )
    parser.add_argument(
        "--backup-confirmed", action="store_true", help="Required with --apply after a fresh DB backup."
    )
    parser.add_argument("--actor-id", type=UUID, help="Teacher/admin user id used as created_by.")
    parser.add_argument("--actor-username", help="Teacher/admin username used as created_by.")
    parser.add_argument(
        "--start-date",
        type=date.fromisoformat,
        default=DEFAULT_START_DATE,
        help="Earliest lesson date for imported lab grades, ISO format YYYY-MM-DD.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


async def run(args: argparse.Namespace) -> int:
    if args.apply and args.parse_only:
        raise SystemExit("--apply cannot be combined with --parse-only")
    if args.apply and not args.backup_confirmed:
        raise SystemExit("--backup-confirmed is required with --apply")
    if args.apply and not (args.actor_id or args.actor_username):
        raise SystemExit("--actor-id or --actor-username is required with --apply")

    entries = parse_grade_notes(args.input)
    if args.parse_only:
        print(json.dumps([asdict(entry) for entry in entries], ensure_ascii=False, default=str, indent=2))
        return 0

    planner = LabGradeImportPlanner(start_date=args.start_date)

    async with AsyncSessionLocal() as db:
        plan = await planner.build_plan(db, entries)
        actor_id = await _resolve_actor_id(db, args) if args.apply else None

        _print_plan(plan, as_json=args.json)
        if not args.apply:
            await db.rollback()
            return 0

        if actor_id is None:
            raise RuntimeError("actor_id is required with --apply")
        applied = await planner.apply_plan(db, plan, actor_id)
        await db.commit()
        print(json.dumps({"applied": applied}, ensure_ascii=False) if args.json else f"Applied: {applied}")
        return 0


async def _resolve_actor_id(db: AsyncSession, args: argparse.Namespace) -> UUID:
    conditions = []
    if args.actor_id:
        conditions.append(User.id == args.actor_id)
    if args.actor_username:
        conditions.append(User.username == args.actor_username)

    result = await db.execute(select(User).where(*conditions))
    user = result.scalar_one_or_none()
    if user is None or user.role not in TEACHER_ROLES:
        raise SystemExit("Actor must be an existing teacher/admin")
    return user.id


def _print_plan(plan: ImportPlan, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(_plan_payload(plan), ensure_ascii=False, default=str, indent=2))
        return

    print(f"Parsed entries: {plan.parsed}")
    print(f"Planned writes: {len(plan.planned)}")
    print(f"Skipped/conflicts: {plan.skipped}")
    for issue in plan.issues[:50]:
        entry = issue.entry
        print(
            f"[skip:{issue.code}] line {entry.line_number}: {entry.group_label or '-'} "
            f"{entry.student_label} {entry.grade}({entry.work_number}) - {issue.message}"
        )
    if len(plan.issues) > 50:
        print(f"... {len(plan.issues) - 50} more issues")


def _plan_payload(plan: ImportPlan) -> dict:
    return {
        "parsed": plan.parsed,
        "planned": [asdict(item) for item in plan.planned],
        "issues": [asdict(issue) for issue in plan.issues],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
