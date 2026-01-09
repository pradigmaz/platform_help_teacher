#!/bin/bash
# ========================================================
# EDU PLATFORM - REBUILD ONLY (uses existing .env)
# ========================================================
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log_info() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_step() { echo -e "\n${BLUE}══════════════════════════════════════════════════════════${NC}"; echo -e "${BLUE}▶ $1${NC}"; }

# Check .env exists
if [ ! -f ".env" ]; then
    log_error ".env не найден! Запустите install.sh для первоначальной настройки."
    exit 1
fi

log_step "Пересборка Edu Platform"

# Stop containers
log_info "Остановка контейнеров..."
docker compose -f docker-compose.prod.yml down 2>/dev/null || true

# Build
log_info "Сборка Docker образов..."
docker compose -f docker-compose.prod.yml build --no-cache

# Start
log_info "Запуск контейнеров..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "⏳ Ожидание запуска сервисов (30 сек)..."
sleep 30

# Check status
FAILED=""
for container in edu-db-prod edu-redis-prod edu-backend-prod edu-frontend-prod; do
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        FAILED="$FAILED $container"
    fi
done

if [ -n "$FAILED" ]; then
    log_error "Не запустились:$FAILED"
    echo "Логи: docker compose -f docker-compose.prod.yml logs"
    exit 1
fi

# Migrations
log_info "Применение миграций..."
docker exec edu-backend-prod alembic upgrade head || log_warn "Migration warning"

log_info "Готово!"
echo ""
echo "Статус:"
docker compose -f docker-compose.prod.yml ps --format "table {{.Name}}\t{{.Status}}"
