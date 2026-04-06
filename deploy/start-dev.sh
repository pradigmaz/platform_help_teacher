#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

compose=(docker compose -f docker-compose.dev.yml --env-file .env.dev)
mode="auto"
reset_frontend_cache=false

while (($# > 0)); do
  case "$1" in
    --build)
      mode="build"
      ;;
    --no-build|--fast)
      mode="no-build"
      ;;
    --clean-next)
      reset_frontend_cache=true
      ;;
    --help|-h)
      cat <<'EOF'
Usage: ./start-dev.sh [--build|--no-build] [--clean-next]
  --build      Force image rebuild before startup.
  --no-build   Start quickly without rebuilding images.
  --fast       Alias for --no-build.
  --clean-next Remove frontend .next caches before startup.
Default mode is auto and rebuilds when dev images are older than
their dependency manifests or Dockerfiles.
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
  shift
done

docker_is_ready() {
  docker info >/dev/null 2>&1
}

image_created_epoch() {
  local image="$1"
  local created="$(docker image inspect --format '{{.Created}}' "$image" 2>/dev/null || true)"
  if [[ -z "$created" ]]; then
    echo 0
    return 0
  fi
  date -d "$created" +%s 2>/dev/null || echo 0
}

latest_mtime() {
  local newest=0
  local path
  for path in "$@"; do
    [[ -e "$path" ]] || continue
    local current
    current="$(stat -c %Y "$path")"
    if (( current > newest )); then
      newest="$current"
    fi
  done
  echo "$newest"
}

needs_rebuild() {
  local image="$1"
  shift
  local image_epoch source_epoch
  image_epoch="$(image_created_epoch "$image")"
  source_epoch="$(latest_mtime "$@")"
  (( image_epoch == 0 || source_epoch > image_epoch ))
}

should_rebuild_images() {
  needs_rebuild \
    "deploy-frontend" \
    "$ROOT_DIR/frontend/Dockerfile.dev" \
    "$ROOT_DIR/frontend/package.json" \
    "$ROOT_DIR/frontend/package-lock.json" \
  || needs_rebuild \
    "deploy-backend" \
    "$ROOT_DIR/backend/Dockerfile.dev" \
    "$ROOT_DIR/backend/requirements.txt"
}

reset_next_cache() {
  local host_cache_dir="$ROOT_DIR/frontend/.next"
  local cleaned_any=false

  if [[ -d "$host_cache_dir" ]]; then
    if rm -rf "$host_cache_dir" 2>/dev/null; then
      echo "Removed frontend host .next cache."
      cleaned_any=true
    else
      echo "Skipped frontend host .next cache cleanup due to permissions."
    fi
  fi

  if docker_is_ready; then
    "${compose[@]}" stop frontend >/dev/null 2>&1 || true
    "${compose[@]}" run --rm --no-deps frontend sh -lc \
      'rm -rf /app/.next/* /app/.next/.[!.]* /app/.next/..?* 2>/dev/null || true'
    echo "Removed frontend container .next cache."
    cleaned_any=true
  fi

  if [[ "$cleaned_any" == false ]]; then
    echo "Frontend cache is already clean."
  fi
}

start_docker_daemon() {
  if docker_is_ready; then
    echo "Docker daemon is already running. Skipping start."
    return 0
  fi
  echo "Docker daemon is not running. Starting it..."
  if command -v systemctl >/dev/null 2>&1; then
    systemctl start docker >/dev/null 2>&1 || sudo systemctl start docker
  elif command -v service >/dev/null 2>&1; then
    service docker start >/dev/null 2>&1 || sudo service docker start
  else
    echo "Unable to start Docker automatically: neither systemctl nor service is available." >&2
    return 1
  fi
  for _ in {1..30}; do
    if docker_is_ready; then
      echo "Docker daemon is running."
      return 0
    fi
    sleep 1
  done
  echo "Docker daemon did not become ready in time." >&2
  return 1
}

start_docker_daemon

if [[ "$reset_frontend_cache" == true ]]; then
  reset_next_cache
fi

if [[ "$mode" == "auto" ]] && should_rebuild_images; then
  mode="build"
  echo "Detected dependency or Dockerfile changes. Rebuilding dev images..."
fi

if [[ "$mode" == "build" ]]; then
  echo "Building and starting dev containers..."
  "${compose[@]}" up -d --build --renew-anon-volumes --remove-orphans
else
  echo "Starting dev containers without rebuilding images..."
  "${compose[@]}" up -d --no-build --remove-orphans
fi

echo "Dev containers are up."
