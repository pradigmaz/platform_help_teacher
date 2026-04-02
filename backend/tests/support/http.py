"""Reusable helpers for router-level HTTP tests without app startup side effects."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.limiter import limiter


def build_router_app(*routers: Any) -> FastAPI:
    """Build a minimal FastAPI app for router-level contract tests."""
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    for router_spec in routers:
        if isinstance(router_spec, tuple):
            router, prefix = router_spec
            app.include_router(router, prefix=prefix)
            continue
        app.include_router(router_spec)
    return app


@asynccontextmanager
async def router_client(*routers: Any, dependency_overrides: dict | None = None) -> AsyncIterator[AsyncClient]:
    """Yield an HTTPX client bound to a minimal FastAPI app with optional dependency overrides."""
    app = build_router_app(*routers)
    if dependency_overrides:
        app.dependency_overrides.update(dependency_overrides)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
