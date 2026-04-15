#!/usr/bin/env bash

DEPLOY_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "$DEPLOY_LIB_DIR/.." && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_step() { echo -e "\n${BLUE}══════════════════════════════════════════════════════════${NC}"; echo -e "${BLUE}▶ $1${NC}"; }
log_skip() { echo -e "${CYAN}[→]${NC} $1"; }

default_prod_env_file() { echo "$DEPLOY_DIR/.env"; }

require_env_file() {
  local env_file="$1"
  if [[ ! -f "$env_file" ]]; then
    log_error "Env file not found: $env_file"
    return 1
  fi
}

load_env_file() {
  local env_file="$1"
  require_env_file "$env_file" || return 1
  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a
}

prod_compose() {
  local env_file="$1"
  shift
  docker compose -f "$DEPLOY_DIR/docker-compose.yml" --env-file "$env_file" "$@"
}

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    log_error "Required command is missing: $command_name"
    return 1
  fi
}

ensure_docker_ready() {
  require_command docker || return 1
  if ! docker info >/dev/null 2>&1; then
    log_error "Docker daemon is not ready."
    return 1
  fi
  if ! docker compose version >/dev/null 2>&1; then
    log_error "Docker Compose is not available."
    return 1
  fi
}

prod_network_name() {
  docker inspect edu-backend-prod --format '{{range $k, $_ := .NetworkSettings.Networks}}{{$k}}{{end}}' 2>/dev/null \
    || echo "${COMPOSE_PROJECT_NAME:-deploy}_backend-net"
}

certbot_volume_name() {
  echo "${COMPOSE_PROJECT_NAME:-deploy}_certbot_data"
}

wait_for_postgres_container() {
  local container_name="$1"
  local pg_user="$2"
  local pg_db="$3"
  local attempts=30

  until docker exec "$container_name" pg_isready -U "$pg_user" -d "$pg_db" >/dev/null 2>&1; do
    attempts=$((attempts - 1))
    if [[ "$attempts" -le 0 ]]; then
      log_error "Postgres container did not become ready: $container_name"
      return 1
    fi
    sleep 1
  done
}
