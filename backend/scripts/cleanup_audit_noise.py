"""Preview or remove known audit noise before a VPS migration."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select

ROOT = Path(__file__).resolve().parents[1]
for candidate in (str(ROOT), "/app"):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from app.audit.models import StudentAuditLog
from app.db.session import AsyncSessionLocal

NOISE_PATH = "/api/v1/auth/csrf-token"
NOISE_ACTION = "view"
NOISE_ROLE = "anonymous"
NOISE_STATUS = 200


def _serialize(value: Any) -> Any:
    if isinstance(value, UUID | datetime):
        return str(value)
    return value


def _build_filters() -> tuple[Any, ...]:
    return (
        StudentAuditLog.path == NOISE_PATH,
        StudentAuditLog.actor_role == NOISE_ROLE,
        StudentAuditLog.response_status == NOISE_STATUS,
        StudentAuditLog.action_type == NOISE_ACTION,
    )


async def _load_summary(session) -> dict[str, Any]:
    filters = _build_filters()
    count_stmt = select(func.count(StudentAuditLog.id)).where(*filters)
    range_stmt = select(
        func.min(StudentAuditLog.created_at),
        func.max(StudentAuditLog.created_at),
    ).where(*filters)
    days_stmt = (
        select(
            func.date_trunc("day", StudentAuditLog.created_at).label("day"),
            func.count(StudentAuditLog.id).label("count"),
        )
        .where(*filters)
        .group_by("day")
        .order_by("day")
    )

    count = (await session.execute(count_stmt)).scalar_one()
    min_created_at, max_created_at = (await session.execute(range_stmt)).one()
    days = [
        {"day": str(row.day), "count": row.count}
        for row in (await session.execute(days_stmt)).all()
    ]

    return {
        "path": NOISE_PATH,
        "actor_role": NOISE_ROLE,
        "response_status": NOISE_STATUS,
        "action_type": NOISE_ACTION,
        "count": count,
        "min_created_at": str(min_created_at) if min_created_at else None,
        "max_created_at": str(max_created_at) if max_created_at else None,
        "by_day": days,
    }


async def _backup_rows(session) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            select(*StudentAuditLog.__table__.c)
            .where(*_build_filters())
            .order_by(StudentAuditLog.created_at.asc(), StudentAuditLog.id.asc())
        )
    ).mappings()
    return [{key: _serialize(value) for key, value in row.items()} for row in rows]


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Preview or clean known csrf-token audit noise.")
    parser.add_argument("--apply", action="store_true", help="Delete the known noise rows.")
    parser.add_argument(
        "--backup-file",
        help="Path to write a JSON backup of the deleted rows. Required with --apply.",
    )
    args = parser.parse_args()

    if args.apply and not args.backup_file:
        parser.error("--backup-file is required with --apply")

    async with AsyncSessionLocal() as session:
        summary = await _load_summary(session)
        print(json.dumps(summary, indent=2, ensure_ascii=False))

        if not args.apply or summary["count"] == 0:
            return

        backup_path = Path(args.backup_file)
        if backup_path.exists():
            raise RuntimeError(f"Backup file already exists: {backup_path}")

        _write_json(backup_path, await _backup_rows(session))
        print(f"\nBackup written to: {backup_path}")

        result = await session.execute(delete(StudentAuditLog).where(*_build_filters()))
        await session.commit()
        print(f"Deleted rows: {result.rowcount or 0}")


if __name__ == "__main__":
    asyncio.run(main())
