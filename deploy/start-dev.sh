#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

compose=(docker compose -f docker-compose.dev.yml --env-file .env.dev)
force_build="${1:-}"

docker_is_ready() {
  docker info >/dev/null 2>&1
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

if [[ "$force_build" == "--build" ]]; then
  echo "Building and starting dev containers..."
  "${compose[@]}" up -d --build
  exit 0
fi

echo "Starting dev containers without rebuilding images..."
"${compose[@]}" up -d --no-build
echo "Dev containers are up."
