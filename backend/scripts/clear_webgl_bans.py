#!/usr/bin/env python3
"""
Скрипт для очистки банов по WebGL fingerprint.
Запуск: docker exec edu-backend python scripts/clear_webgl_bans.py
"""

import asyncio
import redis.asyncio as redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


async def clear_webgl_bans():
    """Удаляет все баны по webgl компоненту."""
    r = await redis.from_url(REDIS_URL)

    # Ищем все ключи с webgl банами
    pattern = "sec:ban:comp:webgl:*"
    cursor = 0
    deleted = 0

    while True:
        cursor, keys = await r.scan(cursor, match=pattern, count=100)
        if keys:
            await r.delete(*keys)
            deleted += len(keys)
            print(f"Удалено {len(keys)} webgl банов")
        if cursor == 0:
            break

    # Также чистим fingerprint баны (они могут содержать webgl)
    fp_pattern = "sec:ban:fp:*"
    cursor = 0

    while True:
        cursor, keys = await r.scan(cursor, match=fp_pattern, count=100)
        if keys:
            await r.delete(*keys)
            deleted += len(keys)
            print(f"Удалено {len(keys)} fingerprint банов")
        if cursor == 0:
            break

    await r.close()
    print(f"\n✅ Всего удалено: {deleted} банов")


if __name__ == "__main__":
    asyncio.run(clear_webgl_bans())
