import logging
import sys
from app.core.config import settings

logger = logging.getLogger(__name__)

def check_deployment_settings():
    env = settings.ENVIRONMENT.lower()
    if env not in ["production", "prod"]:
        logger.info(f"⚠️ Running in {env} mode. Security checks are relaxed.")
        return

    logger.info("🔒 Running PRE-DEPLOYMENT SECURITY CHECKS...")
    errors = []

    if len(settings.SECRET_KEY) < 32 or settings.SECRET_KEY == "dev_secret_key_change_in_prod":
        errors.append("CRITICAL: SECRET_KEY is weak or default!")

    webhook = settings.TELEGRAM_WEBHOOK_URL
    if not webhook:
        errors.append("CRITICAL: TELEGRAM_WEBHOOK_URL is missing!")
    elif "ngrok" in webhook or "localhost" in webhook:
        errors.append(f"CRITICAL: Using dev webhook ({webhook}) in production!")

    if errors:
        for err in errors:
            logger.error(err)
        logger.critical("❌ DEPLOYMENT HALTED.")
        sys.exit(1)
    
    logger.info("✅ Security checks passed.")