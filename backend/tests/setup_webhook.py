#!/usr/bin/env python3
"""
Скрипт для установки Telegram webhook
"""
import asyncio
import logging
from app.bots.telegram_bot import set_webhook

logging.basicConfig(level=logging.INFO)

async def main():
    success = await set_webhook()
    if success:
        print("✅ Webhook успешно установлен!")
    else:
        print("❌ Ошибка установки webhook!")

if __name__ == "__main__":
    asyncio.run(main())