"""CLI wrapper for deterministic legacy journal cleanup."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for candidate in (str(ROOT), "/app"):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from legacy_journal_cleanup_lib import apply_plan, build_plan, print_plan

from app.db.session import AsyncSessionLocal


def json_dump(data: Any, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Cleanup deterministic legacy journal conflicts.")
    parser.add_argument("--apply", action="store_true", help="Apply deterministic cleanup changes.")
    parser.add_argument("--backup-file", help="JSON file for the pre-apply cleanup plan.")
    args = parser.parse_args()

    if args.apply and not args.backup_file:
        parser.error("--backup-file is required with --apply")

    async with AsyncSessionLocal() as session:
        plan = await build_plan(session)
        print_plan(plan)

        if not args.apply:
            return

        backup_path = Path(args.backup_file)
        if backup_path.exists():
            raise RuntimeError(f"Backup file already exists: {backup_path}")
        json_dump(plan, backup_path)
        print(f"\nBackup written to: {backup_path}")

        await session.rollback()
        await apply_plan(session, plan)
        print("\nDeterministic cleanup applied.")

        post_plan = await build_plan(session)
        print("\nPost-check:")
        print_plan(post_plan)


if __name__ == "__main__":
    asyncio.run(main())
