import logging
import time
from collections.abc import Callable
from contextlib import asynccontextmanager, suppress
from typing import cast

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_csrf_protect.exceptions import CsrfProtectError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import select
from starlette.exceptions import HTTPException as StarletteHTTPException
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core.config import settings
from app.core.logging_config import configure_logging

configure_logging(settings.LOG_LEVEL)

from app.api.v1.api import api_router
from app.audit.deps import set_audit_extra
from app.audit.middleware import AuditMiddleware
from app.bots import vk_bot
from app.core.csrf import get_csrf_config  # noqa: F401 - loads config
from app.core.csrf_middleware import CSRFMiddleware
from app.core.limiter import limiter
from app.core.prestart_check import check_deployment_settings
from app.core.redis import close_redis
from app.db.session import AsyncSessionLocal
from app.models import User, UserRole
from app.services.bot.webhook_startup import delete_telegram_webhook, register_telegram_webhook
from app.services.external_api import kis_client
from app.services.pdf_service import pdf_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения.
    """
    check_deployment_settings()
    logger.info("🚀 Application starting...")

    await register_telegram_webhook()

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
                        group_id=None,
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

    # --- LOAD ADMIN IDS FOR RATE LIMIT BYPASS ---
    async with AsyncSessionLocal() as db:
        from app.services.rate_limit.service import load_admin_ids_from_db

        await load_admin_ids_from_db(db)

    yield

    logger.info("🛑 Application shutting down...")
    await vk_bot.stop_longpoll()
    await close_redis()
    await kis_client.close()
    await pdf_service.close()
    with suppress(Exception):
        await delete_telegram_webhook()


# Отключаем Swagger/OpenAPI в production для безопасности
_docs_url = "/docs" if settings.ENVIRONMENT == "development" else None
_openapi_url = "/openapi.json" if settings.ENVIRONMENT == "development" else None

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    debug=settings.ENVIRONMENT == "development",
    docs_url=_docs_url,
    openapi_url=_openapi_url,
    redoc_url=None,  # Отключаем ReDoc везде
)


@app.middleware("http")
async def slow_route_logger(request: Request, call_next):
    threshold_ms = settings.API_SLOW_ROUTE_MS
    if threshold_ms <= 0:
        return await call_next(request)

    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    if duration_ms >= threshold_ms:
        logger.warning(
            "slow_route method=%s path=%s status=%s duration_ms=%.1f threshold_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            threshold_ms,
        )
    return response


# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    cast(Callable[[Request, Exception], Response], _rate_limit_exceeded_handler),
)


# CSRF Protection
@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


# Validation Error Handler — логирует детали ошибок валидации в аудит
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Логирует ошибки валидации в аудит для анализа."""
    # Добавляем детали ошибки в audit extra_data
    error_details = [
        {"loc": list(err.get("loc", [])), "msg": err.get("msg", ""), "type": err.get("type", "")}
        for err in exc.errors()[:5]  # Лимит 5 ошибок
    ]
    set_audit_extra(request, "validation_errors", error_details)

    return JSONResponse(status_code=422, content={"detail": exc.errors()})


# HTTP Exception Handler — логирует 4xx ошибки в аудит
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Логирует HTTP ошибки в аудит."""
    if 400 <= exc.status_code < 500:
        set_audit_extra(request, "error_detail", str(exc.detail)[:200])

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# Global Exception Handler — ловит все необработанные ошибки
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Логирует все необработанные исключения."""
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IP Ban Middleware (блокировка после множества 429)
from app.middleware.ip_ban import IPBanMiddleware

app.add_middleware(IPBanMiddleware)

# Security Monitor Middleware (детекция SQL injection, XSS, IDOR)
from app.middleware.security_monitor import SecurityMonitorMiddleware

app.add_middleware(SecurityMonitorMiddleware)

# Audit Middleware (тихий сбор данных о действиях)
app.add_middleware(AuditMiddleware)

# CSRF Middleware (защита мутирующих запросов)
app.add_middleware(CSRFMiddleware)

# Proxy Headers Middleware (для корректной работы за nginx)
# Доверяем всем хостам, т.к. работаем за nginx в Docker
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
