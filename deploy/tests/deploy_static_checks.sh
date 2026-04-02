#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOY_DIR="$ROOT_DIR/deploy"

TMP_DIR="$(mktemp -d)"
LAST_STDOUT=""
LAST_STDERR=""
LAST_OUTPUT=""

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

run_expect() {
  local expected_code="$1"
  local description="$2"
  shift 2

  local stdout_file="$TMP_DIR/stdout.txt"
  local stderr_file="$TMP_DIR/stderr.txt"
  local exit_code=0

  if "$@" >"$stdout_file" 2>"$stderr_file"; then
    exit_code=0
  else
    exit_code=$?
  fi

  LAST_STDOUT="$(cat "$stdout_file")"
  LAST_STDERR="$(cat "$stderr_file")"
  LAST_OUTPUT="${LAST_STDOUT}"$'\n'"${LAST_STDERR}"

  if [[ "$exit_code" -ne "$expected_code" ]]; then
    echo "FAIL: $description (expected exit $expected_code, got $exit_code)"
    if [[ -n "$LAST_STDOUT" ]]; then
      echo "--- stdout ---"
      printf '%s\n' "$LAST_STDOUT"
    fi
    if [[ -n "$LAST_STDERR" ]]; then
      echo "--- stderr ---"
      printf '%s\n' "$LAST_STDERR"
    fi
    exit 1
  fi

  echo "PASS: $description"
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local description="$3"

  if [[ "$haystack" != *"$needle"* ]]; then
    echo "FAIL: $description"
    echo "Expected to find: $needle"
    echo "--- output ---"
    printf '%s\n' "$haystack"
    exit 1
  fi

  echo "PASS: $description"
}

INVALID_ENV_FILE="$TMP_DIR/invalid.env"
cat >"$INVALID_ENV_FILE" <<'EOF'
FRONTEND_URL=https://example.com
NEXT_PUBLIC_API_URL=https://example.com/api/v1
POSTGRES_USER=test
POSTGRES_PASSWORD=test-password
POSTGRES_DB=test-db
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio-password
SECRET_KEY=test-secret-key-for-static-checks
BACKUP_ENCRYPTION_KEY=test-backup-key-for-static-checks
FIRST_SUPERUSER_ID=12345
FIRST_SUPERUSER_USERNAME=admin
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
SSL_EMAIL=ops@example.com
DOMAIN=example.com
EOF

run_expect 0 "deploy shell syntax" \
  bash -n \
  "$DEPLOY_DIR/install.sh" \
  "$DEPLOY_DIR/rebuild.sh" \
  "$DEPLOY_DIR/recovery.sh" \
  "$DEPLOY_DIR/lib/common.sh" \
  "$DEPLOY_DIR/lib/envfile.sh" \
  "$DEPLOY_DIR/lib/prod_deploy.sh"

run_expect 0 "install help" "$DEPLOY_DIR/install.sh" --help
assert_contains "$LAST_OUTPUT" "Использование:" "install help text"

run_expect 0 "rebuild help" "$DEPLOY_DIR/rebuild.sh" --help
assert_contains "$LAST_OUTPUT" "Usage:" "rebuild help text"

run_expect 0 "recovery help" "$DEPLOY_DIR/recovery.sh" --help
assert_contains "$LAST_OUTPUT" "Usage:" "recovery help text"

run_expect 2 "install unknown option" "$DEPLOY_DIR/install.sh" --bogus
assert_contains "$LAST_OUTPUT" "Неизвестная опция" "install unknown option message"

run_expect 2 "rebuild unknown option" "$DEPLOY_DIR/rebuild.sh" --bogus
assert_contains "$LAST_OUTPUT" "Unknown option" "rebuild unknown option message"

run_expect 2 "recovery unknown option" "$DEPLOY_DIR/recovery.sh" --bogus
assert_contains "$LAST_OUTPUT" "Unknown option" "recovery unknown option message"

run_expect 1 "install missing env file" \
  "$DEPLOY_DIR/install.sh" --non-interactive --env-file "$TMP_DIR/missing.env"
assert_contains "$LAST_OUTPUT" "Env file not found" "install missing env validation"

run_expect 1 "rebuild missing env file" \
  "$DEPLOY_DIR/rebuild.sh" --env-file "$TMP_DIR/missing.env"
assert_contains "$LAST_OUTPUT" "Env file not found" "rebuild missing env validation"

run_expect 2 "recovery requires backup key" \
  "$DEPLOY_DIR/recovery.sh" --env-file "$INVALID_ENV_FILE"
assert_contains "$LAST_OUTPUT" "--backup-key is required" "recovery missing backup key validation"

run_expect 1 "install invalid env validation" \
  "$DEPLOY_DIR/install.sh" --non-interactive --env-file "$INVALID_ENV_FILE"
assert_contains "$LAST_OUTPUT" "Missing required env values" "install invalid env message"

run_expect 1 "rebuild invalid env validation" \
  "$DEPLOY_DIR/rebuild.sh" --env-file "$INVALID_ENV_FILE"
assert_contains "$LAST_OUTPUT" "Missing required env values" "rebuild invalid env message"

run_expect 1 "recovery invalid env validation" \
  "$DEPLOY_DIR/recovery.sh" --backup-key backup.enc --env-file "$INVALID_ENV_FILE"
assert_contains "$LAST_OUTPUT" "Missing required env values" "recovery invalid env message"

echo "All deploy static checks passed."
