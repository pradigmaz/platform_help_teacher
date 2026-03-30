from __future__ import annotations

import subprocess
import sys
from pathlib import Path


DEFAULT_MYPY_ARGS = [
    sys.executable,
    "-m",
    "mypy",
    "app",
    "--hide-error-context",
    "--no-color-output",
    "--no-error-summary",
]


def extract_error_lines(output: str) -> list[str]:
    return sorted({line.strip() for line in output.splitlines() if ": error:" in line})


def read_baseline(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    baseline_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("mypy-baseline.txt")
    if not baseline_path.exists():
        print(f"Baseline file not found: {baseline_path}", file=sys.stderr)
        return 2

    result = subprocess.run(
        DEFAULT_MYPY_ARGS,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode not in (0, 1):
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        return result.returncode

    current_errors = extract_error_lines(result.stdout)
    baseline_errors = read_baseline(baseline_path)

    new_errors = sorted(set(current_errors) - set(baseline_errors))
    resolved_errors = sorted(set(baseline_errors) - set(current_errors))

    if resolved_errors:
        print("Resolved mypy baseline entries:")
        for line in resolved_errors:
            print(f"  - {line}")

    if new_errors:
        print("New mypy regressions:")
        for line in new_errors:
            print(f"  + {line}")
        return 1

    print(f"Mypy baseline check passed: {len(current_errors)} tracked errors, 0 regressions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
