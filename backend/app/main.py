import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi_csrf_protect.exceptions import CsrfProtectError

from app.db.session import AsyncSessionLocal
from app.models import User, UserRole
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.limiter import limiter
from app.core.csrf import get_csrf_config  # noqa: F401 - loads config
from app.core.redis import close_redis
from app.services.external_api import kis_client
from app.services.pdf_service import pdf_service
from app.bots.telegram_bot import bot
from app.bots import vk_bot
from app.core.prestart_check import check_deployment_settings
from app.audit.middleware import AuditMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения.
    """
    check_deployment_settings()
    logger.info("🚀 Application starting...")

    if settings.TELEGRAM_WEBHOOK_URL:
        webhook_url = f"{settings.TELEGRAM_WEBHOOK_URL}/api/v1/webhooks/telegram"
        try:
            await bot.set_webhook(
                url=webhook_url,
                secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query"]
            )
            logger.info("Webhook registered successfully.")
        except Exception as e:
            logger.error(f"CRITICAL: Failed to register Telegram webhook: {e}", exc_info=True)
    
    # --- VK BOT LONG POLL ---
    await vk_bot.start_longpoll()
    
    # --- AUTO-ADMIN SEEDING ---
    if settings.FIRST_SUPERUSER_ID:
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(select(User).where(User.telegram_id == settings.FIRST_SUPERUSER_ID))
                user = result.scalar_one_or_none()
                
                if not user:
                    logger.info("First Superuser not found. Creating...")
                    new_superuser = User(
                        telegram_id=settings.FIRST_SUPERUSER_ID,
                        username=settings.FIRST_SUPERUSER_USERNAME,
                        full_name="Super Admin",
                        role=UserRole.ADMIN,
                        is_active=True,
                        group_id=None
                    )
                    db.add(new_superuser)
                    await db.commit()
                    logger.info("Superuser created successfully!")
                else:
                    if user.role != UserRole.ADMIN:
                        logger.warning("User exists but is not admin. Promoting...")
                        user.role = UserRole.ADMIN
                        db.add(user)
                        await db.commit()
            except Exception as e:
                logger.error(f"Failed to seed superuser: {e}")
    
    yield
    
    logger.info("🛑 Application shutting down...")
    await vk_bot.stop_longpoll()
    await close_redis()
    await kis_client.close()
    await pdf_service.close()
    try:
        await bot.delete_webhook()
    except Exception:
        pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    debug=settings.ENVIRONMENT == "development"
)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CSRF Protection
@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit Middleware (тихий сбор данных о действиях)
app.add_middleware(AuditMiddleware)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}