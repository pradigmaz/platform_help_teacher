#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=lib/envfile.sh
source "$SCRIPT_DIR/lib/envfile.sh"
# shellcheck source=lib/prod_deploy.sh
source "$SCRIPT_DIR/lib/prod_deploy.sh"

ENV_FILE="$(default_prod_env_file)"

while (($# > 0)); do
  case "$1" in
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: ./rebuild.sh [--env-file PATH]"
      exit 0
      ;;
    *)
      log_error "Unknown option: $1"
      exit 2
      ;;
  esac
done

load_env_file "$ENV_FILE"
validate_prod_env
check_prod_prereqs

log_step "Rebuild stack"
build_and_start_prod "$ENV_FILE"
verify_prod_containers "$ENV_FILE"
run_prod_migrations
init_minio_bucket

log_info "Rebuild complete"
prod_compose "$ENV_FILE" ps --format "table {{.Name}}\t{{.Status}}"
