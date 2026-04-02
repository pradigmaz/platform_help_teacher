# Развёртывание на VPS

## Требования
- **RAM**: 4GB минимум (6GB рекомендуется)
- **CPU**: 2 cores
- **Disk**: 20GB SSD
- **OS**: Ubuntu 22.04/24.04 LTS
- **Домен**: направлен на IP сервера

---

## Быстрый старт (чистый VPS)

### 1. Базовая настройка

```bash
# Обновить систему
apt update && apt upgrade -y

# Установить Docker
curl -fsSL https://get.docker.com | sh

# Создать swap (рекомендуется)
fallocate -l 2G /swapfile
chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
sysctl vm.swappiness=10
echo 'vm.swappiness=10' >> /etc/sysctl.conf
```

### 2. SSH ключ для CI/CD

```bash
# Создать ключ
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/deploy_key -N ""

# Добавить в authorized_keys
cat ~/.ssh/deploy_key.pub >> ~/.ssh/authorized_keys

# Скопировать приватный ключ для GitHub Secrets
cat ~/.ssh/deploy_key
```

В GitHub: Settings → Secrets → обновить `SSH_PRIVATE_KEY` и `SSH_HOST`

### 3. Клонировать репозиторий

```bash
cd /root
git clone git@github.com:YOUR_USER/platform_help_teacher.git
cd platform_help_teacher/deploy
```

### 4. Настроить .env

```bash
cp .env.example .env
nano .env
```

Обязательные переменные:
```env
POSTGRES_USER=edu_admin
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=edu_platform

MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=<strong-password>
MINIO_BUCKET_NAME=edu-files

SECRET_KEY=<openssl rand -hex 32>

FRONTEND_URL=https://platform-edu.ru
NEXT_PUBLIC_API_URL=https://platform-edu.ru/api
NEXT_PUBLIC_BOT_URL=https://t.me/YOUR_BOT

TELEGRAM_BOT_TOKEN=<from-BotFather>
TELEGRAM_WEBHOOK_URL=https://platform-edu.ru/api/v1/webhooks/telegram
TELEGRAM_WEBHOOK_SECRET=<random-string>

FIRST_SUPERUSER_ID=<your-telegram-id>
FIRST_SUPERUSER_USERNAME=<your-username>
```

### 5. Выполнить установку приложения

```bash
./install.sh --env-file .env --non-interactive
```

Что делает `install.sh`:

- валидирует env-файл перед стартом deploy-пути
- автоматически запрашивает SSL-сертификат, если включён HTTPS и это не `ngrok`
- собирает и поднимает production-стек
- применяет миграции и инициализирует MinIO

### 6. Проверить disposable recovery rehearsal

```bash
./recovery.sh --env-file .env --backup-key <backup-object-key>
```

`recovery.sh` предназначен только для учебного восстановления в одноразовую БД внутри docker-сети. Не запускайте его против живой production БД.

Опциональные флаги: `--recovery-code CODE`, `--drop-existing`

### 7. Установить автозапуск

```bash
chmod +x install-autostart.sh
./install-autostart.sh
```

---

## Проверка

```bash
# Статический безопасный чек deploy-скриптов
bash deploy/tests/deploy_static_checks.sh

# Статус контейнеров после install/rebuild
docker ps

# Память
docker stats --no-stream

# Логи
docker compose -f docker-compose.yml logs -f backend nginx celery

# Тест HTTPS
curl -I https://platform-edu.ru
```

---

## Обновление (CI/CD делает автоматически)

```bash
cd /root/platform_help_teacher
git pull
cd deploy
./rebuild.sh --env-file .env
```

---

## Troubleshooting

### Nginx не запускается (SSL error)
Проверить `DOMAIN` и `SSL_EMAIL` в `.env`, затем повторить `./install.sh --env-file .env --non-interactive`.

### OOM Killer
```bash
dmesg | grep -i kill
# Увеличить RAM или снизить лимиты в docker-compose
```

### Certbot renewal
Автоматически через контейнер certbot каждые 12 часов.

Ручное обновление:
```bash
docker compose -f docker-compose.yml run --rm certbot renew
docker compose -f docker-compose.yml restart nginx
```
