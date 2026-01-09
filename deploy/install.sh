#!/bin/bash
# ========================================================
# EDU PLATFORM - AUTO DEPLOY INSTALLER
# ========================================================
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ============================================
# FUNCTIONS
# ============================================
log_info() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_step() { echo -e "\n${BLUE}══════════════════════════════════════════════════════════${NC}"; echo -e "${BLUE}▶ $1${NC}"; }

ask() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    echo -ne "${CYAN}$prompt${NC}"
    if [ -n "$default" ]; then
        echo -n " [$default]"
    fi
    echo -n ": "
    read user_input
    
    if [ -z "$user_input" ]; then
        user_input="$default"
    fi
    
    eval "$var_name=\"\$user_input\""
}

ask_yes_no() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    echo -ne "${CYAN}$prompt${NC} "
    if [ "$default" = "y" ]; then
        echo -n "[Y/n]: "
    else
        echo -n "[y/N]: "
    fi
    read answer
    
    if [ -z "$answer" ]; then
        answer="$default"
    fi
    
    if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
        eval "$var_name=true"
    else
        eval "$var_name=false"
    fi
}

validate_domain() {
    local domain="$1"
    # Reject IP addresses
    if [[ "$domain" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        return 1
    fi
    # Basic domain validation
    if [[ "$domain" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*$ ]]; then
        return 0
    fi
    return 1
}

validate_tg_token() {
    local token="$1"
    if [[ "$token" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
        return 0
    fi
    return 1
}

validate_number() {
    local num="$1"
    if [[ "$num" =~ ^[0-9]+$ ]]; then
        return 0
    fi
    return 1
}

check_port() {
    local port="$1"
    if ss -tuln | grep -q ":$port "; then
        return 1
    fi
    return 0
}

# ============================================
# STEP 0: CONFIRMATION
# ============================================
log_step "Шаг 0/8: Подтверждение установки"

echo -e "${YELLOW}⚠️  Это установит Edu Platform с нуля.${NC}"
echo -e "${YELLOW}   Существующие контейнеры edu-* будут остановлены.${NC}"
echo ""
echo -n "Введите 'INSTALL' для продолжения: "
read CONFIRM
if [ "$CONFIRM" != "INSTALL" ]; then
    log_error "Установка отменена."
    exit 1
fi

# Backup existing .env
if [ -f ".env" ]; then
    cp .env ".env.backup.$(date +%Y%m%d_%H%M%S)"
    log_info "Существующий .env сохранён в backup"
fi

# Stop existing containers
log_info "Остановка существующих контейнеров..."
docker compose down 2>/dev/null || true

# ============================================
# STEP 1: CHECK DEPENDENCIES
# ============================================
log_step "Шаг 1/8: Проверка зависимостей"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_warn "Запуск от root — swap и Docker будут настроены напрямую"
    IS_ROOT=true
else
    IS_ROOT=false
fi

# Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker не установлен!"
    echo "Установка Docker..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
    log_warn "Перелогиньтесь и запустите скрипт снова!"
    exit 0
fi
log_info "Docker: $(docker --version)"

# Check Docker group
if ! groups | grep -q docker; then
    log_error "Пользователь не в группе docker!"
    sudo usermod -aG docker $USER
    log_warn "Перелогиньтесь и запустите скрипт снова!"
    exit 0
fi

# Docker Compose
if ! docker compose version &> /dev/null; then
    log_error "Docker Compose не установлен!"
    echo "Установите Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
log_info "Docker Compose: $(docker compose version --short)"

# OpenSSL
if ! command -v openssl &> /dev/null; then
    log_error "OpenSSL не установлен!"
    exit 1
fi
log_info "OpenSSL: OK"

# Check swap
SWAP_SIZE=$(free -m | awk '/^Swap:/ {print $2}')
if [ "$SWAP_SIZE" -lt 1024 ]; then
    log_warn "Swap < 1GB (текущий: ${SWAP_SIZE}MB)"
    ask_yes_no "Создать swap 2GB?" "y" "CREATE_SWAP"
    if [ "$CREATE_SWAP" = "true" ]; then
        log_info "Создание swap 2GB..."
        if [ "$IS_ROOT" = "true" ]; then
            fallocate -l 2G /swapfile
            chmod 600 /swapfile
            mkswap /swapfile
            swapon /swapfile
            echo '/swapfile none swap sw 0 0' >> /etc/fstab
            sysctl vm.swappiness=10
            echo 'vm.swappiness=10' >> /etc/sysctl.conf
        else
            sudo fallocate -l 2G /swapfile
            sudo chmod 600 /swapfile
            sudo mkswap /swapfile
            sudo swapon /swapfile
            echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
            sudo sysctl vm.swappiness=10
            echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
        fi
        log_info "Swap создан: 2GB"
    fi
else
    log_info "Swap: ${SWAP_SIZE}MB"
fi

# Check ports
PORTS_BUSY=""
for port in 80 443; do
    if ! check_port $port; then
        PORTS_BUSY="$PORTS_BUSY $port"
    fi
done
if [ -n "$PORTS_BUSY" ]; then
    log_warn "Порты заняты:$PORTS_BUSY"
    echo "Освободите порты или измените конфигурацию."
fi


# ============================================
# STEP 2: DOMAIN SETUP
# ============================================
log_step "Шаг 2/8: Настройка домена"

echo -e "${YELLOW}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${YELLOW}│  ВАЖНО: Требуется домен (ngrok или собственный)            │${NC}"
echo -e "${YELLOW}│  IP-адреса НЕ поддерживаются!                              │${NC}"
echo -e "${YELLOW}│                                                             │${NC}"
echo -e "${YELLOW}│  Примеры:                                                   │${NC}"
echo -e "${YELLOW}│  • abc123.ngrok-free.app (бесплатный ngrok)                │${NC}"
echo -e "${YELLOW}│  • edu.example.com (собственный домен)                     │${NC}"
echo -e "${YELLOW}└─────────────────────────────────────────────────────────────┘${NC}"
echo ""

while true; do
    echo -ne "${CYAN}Введите домен${NC}: "
    read DOMAIN
    
    if [ -z "$DOMAIN" ]; then
        log_error "Домен обязателен!"
        continue
    fi
    
    if ! validate_domain "$DOMAIN"; then
        log_error "Неверный формат домена или введён IP-адрес!"
        echo "Введите домен, например: myapp.ngrok-free.app"
        continue
    fi
    
    break
done

log_info "Домен: $DOMAIN"

# Determine protocol
if [[ "$DOMAIN" == *"ngrok"* ]]; then
    PROTOCOL="https"
    log_info "Ngrok домен → HTTPS автоматически"
else
    ask_yes_no "Использовать HTTPS?" "y" "USE_HTTPS"
    if [ "$USE_HTTPS" = "true" ]; then
        PROTOCOL="https"
    else
        PROTOCOL="http"
    fi
fi

FRONTEND_URL="${PROTOCOL}://${DOMAIN}"
API_URL="${PROTOCOL}://${DOMAIN}/api/v1"

# ============================================
# STEP 3: BOT SETUP
# ============================================
log_step "Шаг 3/8: Настройка мессенджеров"

echo -e "${YELLOW}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${YELLOW}│  Для авторизации нужен хотя бы ОДИН бот:                   │${NC}"
echo -e "${YELLOW}│  • Telegram бот (рекомендуется)                            │${NC}"
echo -e "${YELLOW}│  • VK бот (опционально)                                    │${NC}"
echo -e "${YELLOW}│                                                             │${NC}"
echo -e "${YELLOW}│  Гайды по созданию:                                        │${NC}"
echo -e "${YELLOW}│  • Telegram: docs/TELEGRAM_BOT_SETUP.md                    │${NC}"
echo -e "${YELLOW}│  • VK: docs/VK_BOT_SETUP.md                                │${NC}"
echo -e "${YELLOW}└─────────────────────────────────────────────────────────────┘${NC}"
echo ""

# --- Telegram Bot ---
HAS_TG_BOT=false
TELEGRAM_BOT_TOKEN=""
TELEGRAM_BOT_USERNAME=""
TELEGRAM_WEBHOOK_SECRET=""
TELEGRAM_WEBHOOK_URL=""
BOT_URL=""

ask_yes_no "Есть Telegram бот?" "y" "HAS_TG_BOT"

if [ "$HAS_TG_BOT" = "true" ]; then
    while true; do
        ask "Токен бота (от @BotFather)" "" "TELEGRAM_BOT_TOKEN"
        if validate_tg_token "$TELEGRAM_BOT_TOKEN"; then
            break
        fi
        log_error "Неверный формат токена! Пример: 123456789:ABCdefGHI..."
    done
    
    ask "Username бота (без @)" "" "TELEGRAM_BOT_USERNAME"
    
    TELEGRAM_WEBHOOK_SECRET=$(openssl rand -hex 16)
    TELEGRAM_WEBHOOK_URL="${PROTOCOL}://${DOMAIN}"
    BOT_URL="https://t.me/${TELEGRAM_BOT_USERNAME}"
    
    log_info "Telegram бот настроен: @${TELEGRAM_BOT_USERNAME}"
fi

# --- VK Bot ---
HAS_VK_BOT=false
VK_BOT_TOKEN=""
VK_GROUP_ID=""

ask_yes_no "Есть VK бот?" "n" "HAS_VK_BOT"

if [ "$HAS_VK_BOT" = "true" ]; then
    while true; do
        ask "ID группы VK" "" "VK_GROUP_ID"
        if validate_number "$VK_GROUP_ID"; then
            break
        fi
        log_error "ID группы должен быть числом!"
    done
    
    ask "Токен группы VK" "" "VK_BOT_TOKEN"
    log_info "VK бот настроен: группа $VK_GROUP_ID"
fi

# --- Check at least one bot ---
if [ "$HAS_TG_BOT" = "false" ] && [ "$HAS_VK_BOT" = "false" ]; then
    echo ""
    log_error "ОШИБКА: Нужен хотя бы один бот для авторизации!"
    echo ""
    echo -e "${CYAN}Создайте Telegram бота:${NC}"
    echo "1. Откройте @BotFather в Telegram"
    echo "2. Отправьте /newbot"
    echo "3. Следуйте инструкциям"
    echo "4. Скопируйте токен"
    echo ""
    echo "Подробнее: docs/TELEGRAM_BOT_SETUP.md"
    echo ""
    echo "Затем запустите скрипт снова."
    exit 1
fi

# ============================================
# STEP 4: ADMIN SETUP
# ============================================
log_step "Шаг 4/8: Настройка администратора"

if [ "$HAS_TG_BOT" = "true" ]; then
    echo "Узнать свой Telegram ID: @userinfobot"
    while true; do
        ask "Ваш Telegram ID" "" "FIRST_SUPERUSER_ID"
        if validate_number "$FIRST_SUPERUSER_ID"; then
            break
        fi
        log_error "ID должен быть числом!"
    done
else
    while true; do
        ask "Ваш VK ID" "" "FIRST_SUPERUSER_ID"
        if validate_number "$FIRST_SUPERUSER_ID"; then
            break
        fi
        log_error "ID должен быть числом!"
    done
fi

FIRST_SUPERUSER_USERNAME="admin"
log_info "Администратор: ID=$FIRST_SUPERUSER_ID"


# ============================================
# STEP 5: GENERATE SECRETS
# ============================================
log_step "Шаг 5/8: Генерация секретов"

# Database
POSTGRES_USER="edu_admin"
POSTGRES_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
POSTGRES_DB="edu_platform"

# MinIO
MINIO_ROOT_USER="minioadmin"
MINIO_ROOT_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
MINIO_BUCKET_NAME="edu-uploads"

# Security keys
SECRET_KEY=$(openssl rand -hex 32)
BACKUP_ENCRYPTION_KEY=$(openssl rand -hex 32)

log_info "Сгенерированы пароли и ключи:"
echo ""
echo -e "  ${CYAN}PostgreSQL:${NC}"
echo "    User: $POSTGRES_USER"
echo "    Password: $POSTGRES_PASSWORD"
echo ""
echo -e "  ${CYAN}MinIO:${NC}"
echo "    User: $MINIO_ROOT_USER"
echo "    Password: $MINIO_ROOT_PASSWORD"
echo ""
echo -e "${YELLOW}⚠️  СОХРАНИТЕ ЭТИ ДАННЫЕ! Они не будут показаны снова.${NC}"
echo ""

# ============================================
# STEP 6: GENERATE .ENV
# ============================================
log_step "Шаг 6/8: Генерация конфигурации"

cat > .env << EOF
# ========================================
# EDU PLATFORM CONFIGURATION
# Generated: $(date)
# ========================================

# Database
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=${POSTGRES_DB}

# MinIO (S3-compatible storage)
MINIO_ROOT_USER=${MINIO_ROOT_USER}
MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}
MINIO_BUCKET_NAME=${MINIO_BUCKET_NAME}

# Backend Security
SECRET_KEY=${SECRET_KEY}
ENVIRONMENT=production
LOG_LEVEL=INFO

# Telegram Bot
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_WEBHOOK_SECRET=${TELEGRAM_WEBHOOK_SECRET}
TELEGRAM_WEBHOOK_URL=${TELEGRAM_WEBHOOK_URL}

# VK Bot
VK_BOT_TOKEN=${VK_BOT_TOKEN}
VK_GROUP_ID=${VK_GROUP_ID}

# Redis
REDIS_URL=redis://redis:6379/0

# Backup Settings
BACKUP_ENCRYPTION_KEY=${BACKUP_ENCRYPTION_KEY}
BACKUP_STORAGE_BUCKET=edu-backups
BACKUP_RETENTION_DAYS=30

# First Admin
FIRST_SUPERUSER_ID=${FIRST_SUPERUSER_ID}
FIRST_SUPERUSER_USERNAME=${FIRST_SUPERUSER_USERNAME}

# Frontend URLs
FRONTEND_URL=${FRONTEND_URL}
NEXT_PUBLIC_API_URL=${API_URL}
NEXT_PUBLIC_BOT_URL=${BOT_URL}
EOF

log_info "Конфигурация сохранена в .env"

# ============================================
# STEP 7: BUILD AND START
# ============================================
log_step "Шаг 7/8: Сборка и запуск"

log_info "Сборка Docker образов..."
docker compose -f docker-compose.prod.yml build

log_info "Запуск контейнеров..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "⏳ Ожидание запуска сервисов (30 сек)..."
sleep 30

# Check container status
FAILED_CONTAINERS=""
for container in edu-db-prod edu-redis-prod edu-minio-prod edu-backend-prod edu-frontend-prod; do
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        FAILED_CONTAINERS="$FAILED_CONTAINERS $container"
    fi
done

if [ -n "$FAILED_CONTAINERS" ]; then
    log_error "Не запустились контейнеры:$FAILED_CONTAINERS"
    echo "Проверьте логи: docker compose -f docker-compose.prod.yml logs"
    exit 1
fi

log_info "Все контейнеры запущены"

# Run migrations
log_info "Применение миграций БД..."
docker exec edu-backend-prod alembic upgrade head || log_warn "Migration warning"

# Initialize MinIO
log_info "Инициализация MinIO бакетов..."
docker exec edu-backend-prod python -c "from app.core.config import settings; from minio import Minio; client = Minio(settings.MINIO_ENDPOINT, settings.MINIO_ROOT_USER, settings.MINIO_ROOT_PASSWORD, secure=False); client.make_bucket(settings.MINIO_BUCKET_NAME) if not client.bucket_exists(settings.MINIO_BUCKET_NAME) else None" || log_warn "MinIO init warning"

# Setup SSL if needed
if [ "$USE_HTTPS" = "true" ] && [[ "$DOMAIN" != *"ngrok"* ]]; then
    log_info "Настройка SSL сертификата..."
    ask "Email для Let's Encrypt" "" "SSL_EMAIL"
    docker compose -f docker-compose.prod.yml run --rm certbot certonly \
        --webroot -w /var/www/certbot \
        -d "$DOMAIN" \
        --email "$SSL_EMAIL" \
        --agree-tos --non-interactive || log_warn "SSL setup failed - настройте вручную"
    docker compose -f docker-compose.prod.yml restart nginx
fi

# ============================================
# STEP 8: FINAL REPORT
# ============================================
log_step "Шаг 8/8: Готово!"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           УСТАНОВКА УСПЕШНО ЗАВЕРШЕНА!                     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}Frontend:${NC}      ${FRONTEND_URL}"
echo -e "  ${CYAN}API Docs:${NC}      ${FRONTEND_URL}/api/docs"
if [ -n "$BOT_URL" ]; then
echo -e "  ${CYAN}Telegram Bot:${NC}  ${BOT_URL}"
fi
echo ""
echo -e "${YELLOW}Учётные данные сохранены в .env${NC}"
echo ""

# Status check
echo -e "${CYAN}Статус сервисов:${NC}"
docker compose -f docker-compose.prod.yml ps --format "table {{.Name}}\t{{.Status}}"
echo ""

# Useful commands
echo -e "${CYAN}Полезные команды:${NC}"
echo "  Логи:      docker compose -f docker-compose.prod.yml logs -f"
echo "  Рестарт:   docker compose -f docker-compose.prod.yml restart"
echo "  Остановка: docker compose -f docker-compose.prod.yml down"
echo ""

log_info "Установка завершена!"
