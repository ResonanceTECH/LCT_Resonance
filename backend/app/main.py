from __future__ import annotations

import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    http_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.core.logging import configure_logging

access_logger = logging.getLogger("app.access")
API_PREFIX = "/api"

# Client-supplied request ids are echoed into logs and headers, so only a safe shape is accepted.
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _request_id_from(request: Request) -> str:
    incoming = request.headers.get("x-request-id", "")
    return incoming if _REQUEST_ID_RE.match(incoming) else f"req_{uuid.uuid4().hex[:12]}"


async def request_context(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = _request_id_from(request)
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    access_logger.info(
        "request",
        extra={
            "request_id": request_id,
            "user_id": getattr(request.state, "user_id", None),
            "route": request.url.path,
            "method": request.method,
            "status": response.status_code,
            "duration_ms": int((time.perf_counter() - started) * 1000),
        },
    )
    return response


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    if settings.is_dev:
        logging.getLogger("app").warning(
            "dev_mode: verification tokens are returned in API responses and cookies are "
            "not Secure; set APP_ENV=prod on a public stand"
        )

    app = FastAPI(
        title="Resonance Backend",
        version=__version__,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        description="Обратный рекрутинг: Talent Pool, Match Score, ФСП, офферы. "
        "Контракт повторяет frontend/src/entities/types.ts (camelCase).",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )
    app.middleware("http")(request_context)

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    app.include_router(api_router, prefix=API_PREFIX)
    return app


app = create_app()
