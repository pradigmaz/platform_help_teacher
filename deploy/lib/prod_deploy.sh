#!/usr/bin/env bash

check_prod_prereqs() {
  ensure_docker_ready || return 1
  require_command openssl || return 1
}

ensure_ssl_certificate() {
  if [[ "${USE_HTTPS:-false}" != true || "${DOMAIN:-}" == *ngrok* ]]; then
    return 0
  fi

  local cert_volume
  cert_volume="$(certbot_volume_name)"
  if docker volume inspect "$cert_volume" >/dev/null 2>&1; then
    if docker run --rm -v "${cert_volume}:/certs" alpine sh -c "test -f /certs/live/$DOMAIN/fullchain.pem" >/dev/null 2>&1; then
      log_skip "SSL certificate for $DOMAIN already exists"
      return 0
    fi
  fi

  local certbot_www="$DEPLOY_DIR/certbot-www"
  local certbot_data="$DEPLOY_DIR/certbot-data"
  mkdir -p "$certbot_www/.well-known/acme-challenge" "$certbot_data"
  docker rm -f temp-nginx >/dev/null 2>&1 || true

  cat > /tmp/acme-nginx.conf <<'NGINX_CONF'
events { worker_connections 128; }
http {
  server {
    listen 80;
    server_name _;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 404; }
  }
}
NGINX_CONF

  docker run -d --name temp-nginx -p 80:80 \
    -v "${certbot_www}:/var/www/certbot:ro" \
    -v "/tmp/acme-nginx.conf:/etc/nginx/nginx.conf:ro" nginx:alpine >/dev/null
  sleep 3

  if ! docker run --rm \
    -v "${certbot_data}:/etc/letsencrypt" \
    -v "${certbot_www}:/var/www/certbot" \
    certbot/certbot certonly \
    --webroot --webroot-path=/var/www/certbot \
    -d "$DOMAIN" \
    --email "$SSL_EMAIL" \
    --agree-tos --non-interactive; then
    docker rm -f temp-nginx >/dev/null 2>&1 || true
    rm -rf "$certbot_www" "$certbot_data"
    log_error "Failed to obtain SSL certificate for $DOMAIN"
    return 1
  fi

  docker rm -f temp-nginx >/dev/null 2>&1 || true
  docker volume create "$cert_volume" >/dev/null
  docker run --rm -v "${certbot_data}:/source:ro" -v "${cert_volume}:/dest" alpine sh -c "cp -r /source/* /dest/"
  rm -rf "$certbot_www" "$certbot_data"
}

build_and_start_prod() {
  local env_file="$1"
  prod_compose "$env_file" down >/dev/null 2>&1 || true
  prod_compose "$env_file" build
  prod_compose "$env_file" up -d
}

verify_prod_containers() {
  local env_file="$1"
  local failed=""
  sleep 15
  for container in edu-db-prod edu-redis-prod edu-minio-prod edu-backend-prod edu-frontend-prod; do
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
      failed="$failed $container"
    fi
  done
  if [[ -n "$failed" ]]; then
    log_error "Failed containers:${failed}"
    prod_compose "$env_file" logs --tail=100
    return 1
  fi
}

run_prod_migrations() {
  docker exec edu-backend-prod alembic upgrade head
}

init_minio_bucket() {
  docker run --rm --network "$(prod_network_name)" \
    -e MC_HOST_minio="http://${MINIO_ROOT_USER}:${MINIO_ROOT_PASSWORD}@minio:9000" \
    minio/mc mb --ignore-existing "minio/${MINIO_BUCKET_NAME}" >/dev/null
}
