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
log_skip() { echo -e "${CYAN}[→]${NC} $1 (пропущено — уже настроено)"; }

# ============================================
# LOAD EXISTING CONFIG
# ============================================
load_existing_env() {
    if [ -f ".env" ]; then
        log_info "Найден существующий .env — загружаю конфигурацию..."
        source .env
        EXISTING_ENV=true
        
        # Extract domain from FRONTEND_URL
        if [ -n "$FRONTEND_URL" ]; then
            DOMAIN=$(echo "$FRONTEND_URL" | sed -E 's|https?://||')
            if [[ "$FRONTEND_URL" == https://* ]]; then
                PROTOCOL="https"
                USE_HTTPS=true
            else
                PROTOCOL="http"
                USE_HTTPS=false
            fi
        fi
        
        # Check what's already configured
        [ -n "$TELEGRAM_BOT_TOKEN" ] && HAS_TG_BOT=true || HAS_TG_BOT=false
        [ -n "$VK_BOT_TOKEN" ] && HAS_VK_BOT=true || HAS_VK_BOT=false
        
        # Extract bot username from BOT_URL
        if [ -n "$NEXT_PUBLIC_BOT_URL" ]; then
            TELEGRAM_BOT_USERNAME=$(echo "$NEXT_PUBLIC_BOT_URL" | sed 's|https://t.me/||')
            BOT_URL="$NEXT_PUBLIC_BOT_URL"
        fi
        
        API_URL="$NEXT_PUBLIC_API_URL"
    else
        EXISTING_ENV=false
    fi
}

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
log_step "Шаг 0/9: Подтверждение установки"

# Load existing config first
load_existing_env

if [ "$EXISTING_ENV" = "true" ]; then
    echo -e "${GREEN}Найдена существующая конфигурация:${NC}"
    echo -e "  Домен: ${CYAN}$DOMAIN${NC}"
    [ "$HAS_TG_BOT" = "true" ] && echo -e "  Telegram: ${CYAN}@$TELEGRAM_BOT_USERNAME${NC}"
    [ "$HAS_VK_BOT" = "true" ] && echo -e "  VK: ${CYAN}группа $VK_GROUP_ID${NC}"
    echo ""
    ask_yes_no "Использовать существующую конфигурацию?" "y" "USE_EXISTING"
    if [ "$USE_EXISTING" = "false" ]; then
        EXISTING_ENV=false
        # Backup old config
        cp .env ".env.backup.$(date +%Y%m%d_%H%M%S)"
    fi
else
    USE_EXISTING=false
fi

echo -e "${YELLOW}⚠️  Это установит Edu Platform.${NC}"
if [ "$USE_EXISTING" = "true" ]; then
    echo -e "${GREEN}   Будет использована существующая конфигурация.${NC}"
else
    echo -e "${YELLOW}   Существующие контейнеры edu-* будут остановлены.${NC}"
fi
echo ""
echo -n "Введите 'INSTALL' для продолжения: "
read CONFIRM
if [ "$CONFIRM" != "INSTALL" ]; then
    log_error "Установка отменена."
    exit 1
fi

# Stop existing containers
log_info "Остановка существующих контейнеров..."
docker compose -f docker-compose.prod.yml down 2>/dev/null || true
docker compose down 2>/dev/null || true

# ============================================
# STEP 1: CHECK DEPENDENCIES
# ============================================
log_step "Шаг 1/9: Проверка зависимостей"

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
log_step "Шаг 2/9: Настройка домена"

if [ "$USE_EXISTING" = "true" ] && [ -n "$DOMAIN" ]; then
    log_skip "Домен: $DOMAIN"
else
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
        USE_HTTPS=false  # ngrok handles SSL
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
fi

# ============================================
# STEP 3: BOT SETUP
# ============================================
log_step "Шаг 3/9: Настройка мессенджеров"

if [ "$USE_EXISTING" = "true" ] && { [ "$HAS_TG_BOT" = "true" ] || [ "$HAS_VK_BOT" = "true" ]; }; then
    [ "$HAS_TG_BOT" = "true" ] && log_skip "Telegram бот: @$TELEGRAM_BOT_USERNAME"
    [ "$HAS_VK_BOT" = "true" ] && log_skip "VK бот: группа $VK_GROUP_ID"
else
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
            echo -ne "${CYAN}Токен бота (от @BotFather)${NC}: "
            read TELEGRAM_BOT_TOKEN
            if validate_tg_token "$TELEGRAM_BOT_TOKEN"; then
                break
            fi
            log_error "Неверный формат токена! Пример: 123456789:ABCdefGHI..."
        done
        
        echo -ne "${CYAN}Username бота (без @)${NC}: "
        read TELEGRAM_BOT_USERNAME
        
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
            echo -ne "${CYAN}ID группы VK${NC}: "
            read VK_GROUP_ID
            if validate_number "$VK_GROUP_ID"; then
                break
            fi
            log_error "ID группы должен быть числом!"
        done
        
        echo -ne "${CYAN}Токен группы VK${NC}: "
        read VK_BOT_TOKEN
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
fi

# ============================================
# STEP 4: ADMIN SETUP
# ============================================
log_step "Шаг 4/9: Настройка администратора"

if [ "$USE_EXISTING" = "true" ] && [ -n "$FIRST_SUPERUSER_ID" ]; then
    log_skip "Администратор: ID=$FIRST_SUPERUSER_ID"
else
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
fi


# ============================================
# STEP 5: GENERATE SECRETS
# ============================================
log_step "Шаг 5/9: Генерация секретов"

if [ "$USE_EXISTING" = "true" ] && [ -n "$SECRET_KEY" ]; then
    log_skip "Секреты уже сгенерированы"
else
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
fi

# ============================================
# STEP 6: GENERATE .ENV
# ============================================
log_step "Шаг 6/9: Генерация конфигурации"

if [ "$USE_EXISTING" = "true" ]; then
    log_skip ".env уже существует"
else
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
fi

# ============================================
# STEP 7: SSL CERTIFICATE
# ============================================
log_step "Шаг 7/9: SSL сертификат"

# Check if SSL cert already exists
SSL_EXISTS=false
if docker volume ls | grep -q "deploy_certbot_data"; then
    # Check if cert files exist in volume
    CERT_CHECK=$(docker run --rm -v deploy_certbot_data:/certs alpine sh -c "ls /certs/live/$DOMAIN/fullchain.pem 2>/dev/null && echo 'exists'" 2>/dev/null)
    if [ "$CERT_CHECK" = "exists" ]; then
        SSL_EXISTS=true
    fi
fi

# SSL setup BEFORE nginx with full config
if [ "$USE_HTTPS" = "true" ] && [[ "$DOMAIN" != *"ngrok"* ]]; then
    if [ "$SSL_EXISTS" = "true" ]; then
        log_skip "SSL сертификат для $DOMAIN уже существует"
    else
        log_info "Получение SSL сертификата (до запуска nginx)..."
        
        ask "Email для Let's Encrypt" "" "SSL_EMAIL"
        
        # Create directories for certbot
        mkdir -p certbot-www certbot-data
        
        # Cleanup any leftover temp-nginx from previous runs
        docker rm -f temp-nginx 2>/dev/null || true
        
        # Start temporary nginx for ACME challenge
        log_info "Запуск временного nginx для проверки домена..."
        
        # Create nginx config for ACME challenge
        cat > /tmp/acme-nginx.conf << 'NGINX_CONF'
events { worker_connections 128; }
http {
    server {
        listen 80;
        server_name _;
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        location / {
            return 404;
        }
    }
}
NGINX_CONF
        
        # Create challenge directory
        mkdir -p certbot-www/.well-known/acme-challenge
        
        docker run -d --name temp-nginx \
            -p 80:80 \
            -v "$(pwd)/certbot-www:/var/www/certbot:ro" \
            -v "/tmp/acme-nginx.conf:/etc/nginx/nginx.conf:ro" \
            nginx:alpine
        
        sleep 3
        
        # Get certificate
        log_info "Запрос сертификата от Let's Encrypt..."
        docker run --rm \
            -v "$(pwd)/certbot-data:/etc/letsencrypt" \
            -v "$(pwd)/certbot-www:/var/www/certbot" \
            certbot/certbot certonly \
            --webroot --webroot-path=/var/www/certbot \
            -d "$DOMAIN" \
            --email "$SSL_EMAIL" \
            --agree-tos --non-interactive
        
        CERT_RESULT=$?
        
        # Stop temporary nginx
        docker stop temp-nginx && docker rm temp-nginx
        
        if [ $CERT_RESULT -ne 0 ]; then
            log_error "Не удалось получить SSL сертификат!"
            echo "Проверьте:"
            echo "  1. Домен $DOMAIN направлен на этот сервер"
            echo "  2. Порт 80 открыт в firewall"
            echo ""
            ask_yes_no "Продолжить без SSL (HTTP only)?" "n" "CONTINUE_NO_SSL"
            if [ "$CONTINUE_NO_SSL" = "false" ]; then
                rm -rf certbot-www certbot-data
                exit 1
            fi
            USE_HTTPS=false
            PROTOCOL="http"
            FRONTEND_URL="${PROTOCOL}://${DOMAIN}"
            API_URL="${PROTOCOL}://${DOMAIN}/api/v1"
        else
            log_info "SSL сертификат получен!"
            
            # Copy certs to docker volume
            log_info "Копирование сертификатов в Docker volume..."
            docker volume create deploy_certbot_data 2>/dev/null || true
            docker run --rm \
                -v "$(pwd)/certbot-data:/source:ro" \
                -v deploy_certbot_data:/dest \
                alpine sh -c "cp -r /source/* /dest/"
            
            # Cleanup temp dirs
            rm -rf certbot-www certbot-data
        fi
    fi
else
    if [[ "$DOMAIN" == *"ngrok"* ]]; then
        log_info "Ngrok домен — SSL не требуется (ngrok предоставляет HTTPS)"
    else
        log_info "HTTP режим — SSL пропущен"
    fi
fi

log_step "Шаг 8/9: Сборка и запуск"

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



# ============================================
# STEP 9: FINAL REPORT
# ============================================
log_step "Шаг 9/9: Готово!"

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
