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
NON_INTERACTIVE=false

print_intro() {
  cat <<EOF
${BLUE}Интерактивная установка production-стека${NC}
Скрипт соберёт основные параметры, обновит env-файл и запустит развёртывание.
Для полностью автоматического запуска используйте: ./install.sh --env-file PATH --non-interactive
EOF
}

ask() {
  local prompt="$1"
  local default="${2:-}"
  local value
  echo -ne "${CYAN}${prompt}${NC}"
  [[ -n "$default" ]] && echo -n " [$default]"
  echo -n ": "
  read -r value
  echo "${value:-$default}"
}

ask_yes_no() {
  local prompt="$1"
  local default="$2"
  local answer
  echo -ne "${CYAN}${prompt}${NC} "
  [[ "$default" == "y" ]] && echo -n "[Д/н]: " || echo -n "[д/Н]: "
  read -r answer
  answer="${answer:-$default}"
  case "$answer" in
    [YyДд]) return 0 ;;
    [NnНн]) return 1 ;;
    *) [[ "$default" == "y" ]] ;;
  esac
}

parse_args() {
  while (($# > 0)); do
    case "$1" in
      --env-file)
        ENV_FILE="$2"
        shift 2
        ;;
      --non-interactive)
        NON_INTERACTIVE=true
        shift
        ;;
      --help|-h)
        cat <<EOF
Использование: ./install.sh [--env-file PATH] [--non-interactive]

  интерактивный режим:
    задаёт вопросы, обновляет deploy/.env и запускает установку

  неинтерактивный режим:
    требует полностью заполненный env-файл и не задаёт вопросов
EOF
        exit 0
        ;;
      *)
        log_error "Неизвестная опция: $1"
        exit 2
        ;;
    esac
  done
}

print_config_summary() {
  echo
  echo "${BLUE}Проверьте параметры установки${NC}"
  echo "Домен: ${DOMAIN}"
  echo "Базовый URL: ${FRONTEND_URL}"
  echo "API: ${NEXT_PUBLIC_API_URL}"
  if [[ -n "${NEXT_PUBLIC_BOT_URL:-}" ]]; then
    echo "Telegram-бот: ${NEXT_PUBLIC_BOT_URL}"
  fi
  if [[ -n "${VK_GROUP_ID:-}" ]]; then
    echo "VK: настроен (group id ${VK_GROUP_ID})"
  else
    echo "VK: отключён"
  fi
  echo "Env-файл: ${ENV_FILE}"
}

collect_interactive_inputs() {
  print_intro

  if [[ -f "$ENV_FILE" ]] && ask_yes_no "Использовать существующий env-файл $ENV_FILE?" "y"; then
    load_env_file "$ENV_FILE"
    normalize_prod_env
    log_info "Загружена текущая конфигурация из $ENV_FILE"
    return 0
  fi

  mkdir -p "$(dirname "$ENV_FILE")"
  if [[ -f "$ENV_FILE" ]]; then
    cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    log_info "Создана резервная копия текущего env-файла"
  fi

  DOMAIN="$(ask 'Домен проекта (ngrok или ваш домен)' "${DOMAIN:-}")"
  if ! validate_domain "$DOMAIN"; then
    log_error "Некорректный формат домена."
    exit 2
  fi

  if [[ "$DOMAIN" == *ngrok* ]]; then
    FRONTEND_URL="https://${DOMAIN}"
  elif ask_yes_no "Использовать HTTPS?" "y"; then
    FRONTEND_URL="https://${DOMAIN}"
  else
    FRONTEND_URL="http://${DOMAIN}"
  fi
  NEXT_PUBLIC_API_URL="${FRONTEND_URL}/api/v1"

  TELEGRAM_BOT_TOKEN="$(ask 'Токен Telegram-бота (обязательно)' "${TELEGRAM_BOT_TOKEN:-}")"
  TELEGRAM_WEBHOOK_SECRET="${TELEGRAM_WEBHOOK_SECRET:-$(openssl rand -hex 16)}"
  local bot_username
  bot_username="$(ask 'Username Telegram-бота без @' "${TELEGRAM_BOT_USERNAME:-}")"
  [[ -n "$bot_username" ]] && NEXT_PUBLIC_BOT_URL="https://t.me/${bot_username}"

  if ask_yes_no "Настроить VK-бота?" "n"; then
    VK_GROUP_ID="$(ask 'ID группы VK' "${VK_GROUP_ID:-}")"
    VK_BOT_TOKEN="$(ask 'Токен VK-бота' "${VK_BOT_TOKEN:-}")"
  else
    VK_GROUP_ID=""
    VK_BOT_TOKEN=""
  fi

  FIRST_SUPERUSER_ID="$(ask 'ID администратора в Telegram/VK' "${FIRST_SUPERUSER_ID:-}")"
  POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -base64 16 | tr -d '=+/' | cut -c1-16)}"
  MINIO_ROOT_USER="${MINIO_ROOT_USER:-minioadmin}"
  MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-$(openssl rand -base64 16 | tr -d '=+/' | cut -c1-16)}"
  SECRET_KEY="${SECRET_KEY:-$(openssl rand -hex 32)}"
  BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-$(openssl rand -hex 32)}"

  if [[ "$FRONTEND_URL" == https://* && "$DOMAIN" != *ngrok* ]]; then
    SSL_EMAIL="$(ask "Email для Let's Encrypt" "${SSL_EMAIL:-}")"
  fi

  validate_prod_env
  print_config_summary
  if ! ask_yes_no "Записать эти настройки и продолжить установку?" "y"; then
    log_info "Установка отменена до записи конфигурации."
    exit 0
  fi
  write_prod_env "$ENV_FILE"
  log_info "Env-файл сохранён: $ENV_FILE"
}

run_install() {
  load_env_file "$ENV_FILE"
  validate_prod_env
  check_prod_prereqs

  log_step "Подготовка SSL"
  ensure_ssl_certificate

  log_step "Сборка и запуск стека"
  build_and_start_prod "$ENV_FILE"

  log_step "Проверка сервисов"
  verify_prod_containers "$ENV_FILE"

  log_step "Применение миграций"
  run_prod_migrations

  log_step "Инициализация MinIO"
  init_minio_bucket

  log_step "Установка завершена"
  echo "Фронтенд: ${FRONTEND_URL}"
  echo "Документация API: ${FRONTEND_URL}/api/docs"
  [[ -n "${NEXT_PUBLIC_BOT_URL:-}" ]] && echo "Telegram-бот: ${NEXT_PUBLIC_BOT_URL}"
  echo "Env-файл: $ENV_FILE"
  prod_compose "$ENV_FILE" ps --format "table {{.Name}}\t{{.Status}}"
}

parse_args "$@"
if [[ "$NON_INTERACTIVE" == true ]]; then
  run_install
else
  collect_interactive_inputs
  run_install
fi
