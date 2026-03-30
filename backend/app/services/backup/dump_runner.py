"""
PostgreSQL dump and restore helpers for backup flows.
"""

import asyncio
import contextlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.core.time_constants import BACKUP_DUMP_TIMEOUT_SECONDS


@dataclass(frozen=True)
class PostgresConnectionConfig:
    host: str
    user: str
    password: str
    dbname: str
    port: int = 5432


def default_postgres_connection() -> PostgresConnectionConfig:
    return PostgresConnectionConfig(
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DB,
    )


def _build_pgpass_content(config: PostgresConnectionConfig) -> str:
    return f"{config.host}:{config.port}:{config.dbname}:{config.user}:{config.password}"


@contextlib.contextmanager
def temporary_pgpass(directory: Path, config: PostgresConnectionConfig):
    pgpass_path = directory / ".pgpass"
    pgpass_path.write_text(_build_pgpass_content(config))
    os.chmod(pgpass_path, 0o600)
    try:
        yield {"PGPASSFILE": str(pgpass_path)}
    finally:
        pgpass_path.unlink(missing_ok=True)


async def _run_async_command(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    error_prefix: str,
) -> tuple[str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=BACKUP_DUMP_TIMEOUT_SECONDS)
    except TimeoutError as exc:
        with contextlib.suppress(ProcessLookupError):
            proc.kill()
        with contextlib.suppress(ProcessLookupError):
            await proc.wait()
        raise RuntimeError(f"{error_prefix} timed out after {BACKUP_DUMP_TIMEOUT_SECONDS} seconds") from exc

    stdout_text = stdout.decode(errors="replace")
    stderr_text = stderr.decode(errors="replace")
    if proc.returncode != 0:
        details = stderr_text.strip() or stdout_text.strip() or f"exit code {proc.returncode}"
        raise RuntimeError(f"{error_prefix} failed: {details}")
    return stdout_text, stderr_text


def _run_sync_command(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    error_prefix: str,
) -> None:
    result = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        timeout=BACKUP_DUMP_TIMEOUT_SECONDS,
        check=False,
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
        raise RuntimeError(f"{error_prefix} failed: {details}")


async def run_pg_dump(output_path: Path, config: PostgresConnectionConfig) -> None:
    with temporary_pgpass(output_path.parent, config) as pg_env:
        await _run_async_command(
            [
                "pg_dump",
                "--format=custom",
                "--no-password",
                f"--host={config.host}",
                f"--port={config.port}",
                f"--username={config.user}",
                f"--dbname={config.dbname}",
                f"--file={output_path}",
            ],
            env={**dict(os.environ), **pg_env},
            error_prefix="pg_dump",
        )


def run_pg_dump_sync(output_path: Path, config: PostgresConnectionConfig) -> None:
    with temporary_pgpass(output_path.parent, config) as pg_env:
        _run_sync_command(
            [
                "pg_dump",
                "--format=custom",
                "--no-password",
                f"--host={config.host}",
                f"--port={config.port}",
                f"--username={config.user}",
                f"--dbname={config.dbname}",
                f"--file={output_path}",
            ],
            env={**dict(os.environ), **pg_env},
            error_prefix="pg_dump",
        )


async def run_pg_restore(
    dump_path: Path,
    config: PostgresConnectionConfig,
    *,
    drop_existing: bool,
) -> None:
    with temporary_pgpass(dump_path.parent, config) as pg_env:
        cmd = [
            "pg_restore",
            "--no-password",
            f"--host={config.host}",
            f"--port={config.port}",
            f"--username={config.user}",
            f"--dbname={config.dbname}",
            "--no-owner",
            "--no-privileges",
        ]
        if drop_existing:
            cmd.extend(["--clean", "--if-exists"])
        cmd.append(str(dump_path))
        await _run_async_command(
            cmd,
            env={**dict(os.environ), **pg_env},
            error_prefix="pg_restore",
        )


async def verify_dump(dump_path: Path) -> None:
    await _run_async_command(
        ["pg_restore", "--list", str(dump_path)],
        env=dict(os.environ),
        error_prefix="pg_restore --list",
    )
