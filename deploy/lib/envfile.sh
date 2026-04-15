#!/usr/bin/env bash

seed_prod_defaults() {
  : "${POSTGRES_USER:=edu_admin}"
  : "${POSTGRES_DB:=edu_platform}"
  : "${MINIO_BUCKET_NAME:=edu-uploads}"
  : "${BACKUP_STORAGE_BUCKET:=edu-backups}"
  : "${BACKUP_RETENTION_DAYS:=30}"
  : "${FIRST_SUPERUSER_USERNAME:=admin}"
}

normalize_prod_env() {
  seed_prod_defaults

  if [[ -n "${FRONTEND_URL:-}" && -z "${NEXT_PUBLIC_API_URL:-}" ]]; then
    NEXT_PUBLIC_API_URL="${FRONTEND_URL%/}/api/v1"
  fi
  if [[ -n "${FRONTEND_URL:-}" && -z "${TELEGRAM_WEBHOOK_URL:-}" ]]; then
    TELEGRAM_WEBHOOK_URL="$FRONTEND_URL"
  fi
  if [[ -n "${FRONTEND_URL:-}" && -z "${DOMAIN:-}" ]]; then
    DOMAIN="${FRONTEND_URL#http://}"
    DOMAIN="${DOMAIN#https://}"
  fi
  if [[ -n "${FRONTEND_URL:-}" ]]; then
    if [[ "$FRONTEND_URL" == https://* ]]; then
      USE_HTTPS=true
    else
      USE_HTTPS=false
    fi
  fi
}

validate_domain() {
  local domain="$1"
  [[ "$domain" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] && return 1
  [[ "$domain" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*$ ]]
}

validate_tg_token() {
  [[ "$1" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]
}

validate_number() {
  [[ "$1" =~ ^[0-9]+$ ]]
}

validate_prod_env() {
  normalize_prod_env
  local missing=()
  local required=(
    FRONTEND_URL NEXT_PUBLIC_API_URL
    POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB
    MINIO_ROOT_USER MINIO_ROOT_PASSWORD
    SECRET_KEY BACKUP_ENCRYPTION_KEY
    FIRST_SUPERUSER_ID FIRST_SUPERUSER_USERNAME
    TELEGRAM_BOT_TOKEN TELEGRAM_WEBHOOK_SECRET
  )

  for key in "${required[@]}"; do
    [[ -n "${!key:-}" ]] || missing+=("$key")
  done
  if [[ -n "${VK_BOT_TOKEN:-}" && -z "${VK_GROUP_ID:-}" ]]; then
    missing+=("VK_GROUP_ID")
  fi
  if [[ "${USE_HTTPS:-false}" == true && "${DOMAIN:-}" != *ngrok* && -z "${SSL_EMAIL:-}" ]]; then
    missing+=("SSL_EMAIL")
  fi
  if [[ -n "${DOMAIN:-}" ]] && ! validate_domain "$DOMAIN"; then
    log_error "Invalid DOMAIN value: $DOMAIN"
    return 1
  fi
  if [[ -n "${FIRST_SUPERUSER_ID:-}" ]] && ! validate_number "$FIRST_SUPERUSER_ID"; then
    log_error "FIRST_SUPERUSER_ID must be numeric"
    return 1
  fi
  if [[ -n "${TELEGRAM_BOT_TOKEN:-}" ]] && ! validate_tg_token "$TELEGRAM_BOT_TOKEN"; then
    log_error "TELEGRAM_BOT_TOKEN has invalid format"
    return 1
  fi
  if [[ "${#missing[@]}" -gt 0 ]]; then
    log_error "Missing required env values: ${missing[*]}"
    return 1
  fi
}

write_prod_env() {
  local env_file="$1"
  normalize_prod_env
  cat >"$env_file" <<EOF
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=${POSTGRES_DB}
MINIO_ROOT_USER=${MINIO_ROOT_USER}
MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}
MINIO_BUCKET_NAME=${MINIO_BUCKET_NAME}
SECRET_KEY=${SECRET_KEY}
ENVIRONMENT=production
LOG_LEVEL=${LOG_LEVEL:-INFO}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-}
TELEGRAM_WEBHOOK_SECRET=${TELEGRAM_WEBHOOK_SECRET:-}
TELEGRAM_WEBHOOK_URL=${TELEGRAM_WEBHOOK_URL:-}
VK_BOT_TOKEN=${VK_BOT_TOKEN:-}
VK_GROUP_ID=${VK_GROUP_ID:-}
REDIS_URL=${REDIS_URL:-redis://redis:6379/0}
BACKUP_ENCRYPTION_KEY=${BACKUP_ENCRYPTION_KEY}
BACKUP_STORAGE_BUCKET=${BACKUP_STORAGE_BUCKET}
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS}
FIRST_SUPERUSER_ID=${FIRST_SUPERUSER_ID}
FIRST_SUPERUSER_USERNAME=${FIRST_SUPERUSER_USERNAME}
FRONTEND_FINGERPRINT_MODE=${FRONTEND_FINGERPRINT_MODE:-off}
FRONTEND_URL=${FRONTEND_URL}
NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
NEXT_PUBLIC_BOT_URL=${NEXT_PUBLIC_BOT_URL:-}
SSL_EMAIL=${SSL_EMAIL:-}
DOMAIN=${DOMAIN:-}
EOF
}
