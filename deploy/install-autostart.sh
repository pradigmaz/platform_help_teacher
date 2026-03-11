#!/bin/bash
# Установка автозапуска Edu Platform при загрузке VPS

set -e

SERVICE_FILE="edu-platform.service"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "📦 Установка systemd сервиса..."

# Копируем service файл
sudo cp "$SCRIPT_DIR/$SERVICE_FILE" /etc/systemd/system/

# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable edu-platform.service

echo ""
echo "✅ Готово! Команды управления:"
echo ""
echo "  systemctl start edu-platform    # Запустить"
echo "  systemctl stop edu-platform     # Остановить"
echo "  systemctl restart edu-platform  # Перезапустить"
echo "  systemctl status edu-platform   # Статус"
echo "  cd $SCRIPT_DIR && docker compose -f docker-compose.yml logs -f  # Логи контейнеров"
echo ""
echo "🔄 Платформа будет автоматически запускаться при перезагрузке VPS"
