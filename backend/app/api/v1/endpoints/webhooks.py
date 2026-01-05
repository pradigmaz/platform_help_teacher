import logging
import ipaddress
from fastapi import APIRouter, Header, HTTPException, Request, status, Depends
from aiogram import types
from app.core.config import settings
from app.core.limiter import limiter
from app.bots.telegram_bot import bot, dp
from app.api import deps

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/telegram", dependencies=[Depends(deps.verify_telegram_ip)])
@limiter.limit("100/minute")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None)
):
    """
    Эндпоинт для получения обновлений от Telegram через Webhook.
    """
    # IP Security Check moved to dependency verify_telegram_ip

    # Валидация секретного токена
    if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        # SECURITY FIX: Don't log the actual wrong token
        logger.warning("Invalid secret token received (masked: ***)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid secret token"
        )

    try:
        # Обработка обновления
        update_data = await request.json()
        
        update = types.Update(**update_data)
        
        await dp.feed_webhook_update(bot, update)
        logger.info(f"Update {update.update_id} processed successfully")
        
        return {"status": "ok"}
    except ValueError as e:
        # Invalid JSON or Update format - client error, don't retry
        logger.warning(f"Invalid update format: {e}")
        raise HTTPException(status_code=400, detail="Invalid update format")
    except Exception as e:
        logger.error(f"Error processing telegram update: {e}", exc_info=True)
        # Return 500 so Telegram knows to retry
        raise HTTPException(status_code=500, detail="Internal processing error")

@router.get("/status")
async def get_webhook_status():
    """
    Проверка статуса вебхука через Telegram API.
    """
    try:
        webhook_info = await bot.get_webhook_info()
        return {
            "status": "ok",
            "webhook_info": {
                "url": webhook_info.url,
                "has_custom_certificate": webhook_info.has_custom_certificate,
                "pending_update_count": webhook_info.pending_update_count,
                "ip_address": webhook_info.ip_address,
                "last_error_date": webhook_info.last_error_date,
                "last_error_message": webhook_info.last_error_message,
                "max_connections": webhook_info.max_connections,
                "allowed_updates": webhook_info.allowed_updates
            }
        }
    except Exception as e:
        logger.error(f"Failed to get webhook info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get webhook info")
