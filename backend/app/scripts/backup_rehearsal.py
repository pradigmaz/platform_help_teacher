"""
CLI helpers for deterministic backup restore rehearsals.
"""

import argparse
import asyncio
import json
from typing import Sequence

from app.services.backup.dump_runner import PostgresConnectionConfig
from app.services.backup.restore_service import RestoreService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backup rehearsal helpers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    restore_smoke = subparsers.add_parser("restore-smoke", help="Restore a backup into a disposable target database")
    restore_smoke.add_argument("--backup-key", required=True)
    restore_smoke.add_argument("--target-db-host", required=True)
    restore_smoke.add_argument("--target-db-port", required=False, type=int, default=5432)
    restore_smoke.add_argument("--target-db-name", required=True)
    restore_smoke.add_argument("--target-db-user", required=True)
    restore_smoke.add_argument("--target-db-password", required=True)
    restore_smoke.add_argument("--recovery-code")
    restore_smoke.add_argument("--drop-existing", action="store_true")
    return parser


async def run_restore_smoke(args: argparse.Namespace) -> int:
    service = RestoreService()
    result = await service.restore_backup_to_target(
        args.backup_key,
        target=PostgresConnectionConfig(
            host=args.target_db_host,
            port=args.target_db_port,
            user=args.target_db_user,
            password=args.target_db_password,
            dbname=args.target_db_name,
        ),
        drop_existing=args.drop_existing,
        recovery_code=args.recovery_code,
    )
    print(
        json.dumps(
            {
                "success": result.success,
                "status": result.status,
                "error": result.error,
                "offsite_used": result.offsite_used,
                "portable": result.portable,
                "format_version": result.format_version,
            },
            ensure_ascii=True,
        )
    )
    return 0 if result.success else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "restore-smoke":
        return asyncio.run(run_restore_smoke(args))
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
