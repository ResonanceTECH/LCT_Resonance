from __future__ import annotations

import time
import uuid
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import health
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    http_error_handler,
    validation_error_handler,
)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Resonance Backend",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("x-request-id", f"req_{uuid.uuid4().hex[:12]}")
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - started) * 1000)
        response.headers["X-Request-Id"] = request_id
        print(
            {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "level": "INFO",
                "request_id": request_id,
                "user_id": getattr(request.state, "user_id", None),
                "route": request.url.path,
                "method": request.method,
                "status": response.status_code,
                "duration_ms": duration_ms,
            }
        )
        return response

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    app.include_router(health.router)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
