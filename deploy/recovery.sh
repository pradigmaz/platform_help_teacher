#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=lib/envfile.sh
source "$SCRIPT_DIR/lib/envfile.sh"

ENV_FILE="$(default_prod_env_file)"
BACKUP_KEY=""
RECOVERY_CODE=""
DROP_EXISTING=false

while (($# > 0)); do
  case "$1" in
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --backup-key)
      BACKUP_KEY="$2"
      shift 2
      ;;
    --recovery-code)
      RECOVERY_CODE="$2"
      shift 2
      ;;
    --drop-existing)
      DROP_EXISTING=true
      shift
      ;;
    --help|-h)
      cat <<EOF
Usage: ./recovery.sh --backup-key KEY [--recovery-code CODE] [--drop-existing] [--env-file PATH]
Runs a disposable restore smoke using the production backend image and a temporary Postgres container.
EOF
      exit 0
      ;;
    *)
      log_error "Unknown option: $1"
      exit 2
      ;;
  esac
done

[[ -n "$BACKUP_KEY" ]] || { log_error "--backup-key is required"; exit 2; }

load_env_file "$ENV_FILE"
validate_prod_env
check_prod_prereqs

SMOKE_CONTAINER="edu-restore-smoke-$(date +%s)"
SMOKE_DB="restore_smoke"
SMOKE_USER="restore_smoke"
SMOKE_PASSWORD="$(openssl rand -hex 16)"
NETWORK_NAME="$(prod_network_name)"

if ! docker image inspect edu-backend:prod >/dev/null 2>&1; then
  log_error "Backend image edu-backend:prod is missing. Run ./deploy/install.sh or ./deploy/rebuild.sh first."
  exit 1
fi
if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
  log_error "Production network is missing: $NETWORK_NAME"
  exit 1
fi

cleanup() {
  docker rm -f "$SMOKE_CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

log_step "Start disposable Postgres"
docker run -d --name "$SMOKE_CONTAINER" --network "$NETWORK_NAME" \
  -e POSTGRES_DB="$SMOKE_DB" \
  -e POSTGRES_USER="$SMOKE_USER" \
  -e POSTGRES_PASSWORD="$SMOKE_PASSWORD" \
  postgres:16-alpine >/dev/null

wait_for_postgres_container "$SMOKE_CONTAINER" "$SMOKE_USER" "$SMOKE_DB"

log_step "Run restore smoke"
docker_cmd=(
  docker run --rm --network "$NETWORK_NAME" --env-file "$ENV_FILE"
  -e POSTGRES_SERVER="$SMOKE_CONTAINER"
  -e POSTGRES_PORT=5432
  -e POSTGRES_DB="$SMOKE_DB"
  -e POSTGRES_USER="$SMOKE_USER"
  -e POSTGRES_PASSWORD="$SMOKE_PASSWORD"
  edu-backend:prod
  python -m app.scripts.backup_rehearsal restore-smoke
  --backup-key "$BACKUP_KEY"
  --target-db-host "$SMOKE_CONTAINER"
  --target-db-port 5432
  --target-db-name "$SMOKE_DB"
  --target-db-user "$SMOKE_USER"
  --target-db-password "$SMOKE_PASSWORD"
)

[[ -n "$RECOVERY_CODE" ]] && docker_cmd+=(--recovery-code "$RECOVERY_CODE")
[[ "$DROP_EXISTING" == true ]] && docker_cmd+=(--drop-existing)

"${docker_cmd[@]}"
log_info "Disposable restore smoke finished successfully"
