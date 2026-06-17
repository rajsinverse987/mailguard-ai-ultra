"""FastAPI application factory."""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

import orjson
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import MailGuardError
from app.core.logging import configure_logging, get_logger
from app.db.redis import close_redis

configure_logging()
logger = get_logger(__name__)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency", ["method", "path"]
)
REQUESTS_TOTAL = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_starting", env=settings.app_env, name=settings.app_name)
    yield
    logger.info("app_stopping")
    await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "MailGuard AI Ultra — AI email intelligence with WhatsApp voice alerts. "
            "OpenAPI docs auto-generated."
        ),
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [settings.app_base_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        REQUEST_LATENCY.labels(method=request.method, path=request.url.path).observe(elapsed)
        REQUESTS_TOTAL.labels(
            method=request.method, path=request.url.path, status=response.status_code
        ).inc()
        response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        return response

    @app.exception_handler(MailGuardError)
    async def domain_exception_handler(_: Request, exc: MailGuardError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, Any]:
        return {"status": "ok", "app": settings.app_name, "env": settings.app_env}

    @app.get("/metrics", tags=["meta"])
    async def metrics() -> Any:
        return generate_latest()

    @app.get("/", tags=["meta"])
    async def root() -> dict[str, Any]:
        return {
            "name": settings.app_name,
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    app.include_router(api_router)
    return app


app = create_app()
