# Создание Telegram бота

## Шаг 1: Откройте @BotFather

Перейдите в Telegram и найдите бота [@BotFather](https://t.me/BotFather).

## Шаг 2: Создайте нового бота

1. Отправьте команду `/newbot`
2. Введите **имя** бота (отображаемое имя, например: "Edu Platform")
3. Введите **username** бота (должен заканчиваться на `bot`, например: `edu_platform_bot`)

## Шаг 3: Сохраните токен

После создания BotFather пришлёт сообщение с токеном:

```
Done! Congratulations on your new bot. You will find it at t.me/edu_platform_bot.
Use this token to access the HTTP API:
123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

**Сохраните этот токен** — он понадобится при установке.

## Шаг 4: Узнайте свой Telegram ID

Для настройки администратора нужен ваш Telegram ID:

1. Откройте бота [@userinfobot](https://t.me/userinfobot)
2. Нажмите "Start"
3. Бот пришлёт ваш ID (число, например: `123456789`)

## Готово!

При запуске `install.sh` вам понадобятся:
- **Токен бота**: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
- **Username бота**: `edu_platform_bot` (без @)
- **Ваш Telegram ID**: `123456789`
