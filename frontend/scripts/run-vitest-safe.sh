#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
VITEST_BIN="$ROOT_DIR/node_modules/.bin/vitest"

if [ ! -x "$VITEST_BIN" ]; then
  echo "vitest binary not found: $VITEST_BIN" >&2
  exit 1
fi

COMBINED_NODE_OPTIONS="--max-old-space-size=1024"
if [ -n "${NODE_OPTIONS:-}" ]; then
  COMBINED_NODE_OPTIONS="${NODE_OPTIONS} ${COMBINED_NODE_OPTIONS}"
fi

run_direct() {
  exec env "NODE_OPTIONS=$COMBINED_NODE_OPTIONS" \
    "$VITEST_BIN" --run --logHeapUsage "$@"
}

if ! command -v systemd-run >/dev/null 2>&1; then
  run_direct "$@"
fi

if [ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
  run_direct "$@"
fi

USER_STATE="$(systemctl --user is-system-running 2>/dev/null || true)"
case "$USER_STATE" in
  running|degraded|starting|maintenance)
    ;;
  *)
    run_direct "$@"
    ;;
esac

exec systemd-run --user --scope --quiet --same-dir \
  -p MemoryHigh=6G \
  -p MemoryMax=7G \
  -p MemorySwapMax=2G \
  env "NODE_OPTIONS=$COMBINED_NODE_OPTIONS" \
  "$VITEST_BIN" --run --logHeapUsage "$@"
