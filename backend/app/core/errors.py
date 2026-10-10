"""Unified error format (Backend.md, "HTTP validation"):

    {"message": "...", "code": "SOME_CODE", "details": {}, "requestId": "req_..."}

The frontend shows `message` as is, so messages are in Russian; `code` is for logic.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.errors")


class AppError(Exception):
    """Business error rendered in the unified format."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.headers = headers
        super().__init__(message)


def error_body(
    code: str, message: str, request_id: str, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {"message": message, "code": code, "details": details or {}, "requestId": request_id}


def integrity_constraint_name(exc: IntegrityError) -> str | None:
    """Name of the violated DB constraint; asyncpg and psycopg expose it differently."""
    orig = exc.orig
    return (
        getattr(orig, "constraint_name", None)
        or getattr(getattr(orig, "diag", None), "constraint_name", None)
        or getattr(getattr(orig, "__cause__", None), "constraint_name", None)
    )


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_body(code, message, _request_id(request), details),
        headers=headers,
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return _error_response(
        request, exc.status_code, exc.code, exc.message, exc.details, exc.headers
    )


_HTTP_MESSAGES = {404: "Не найдено", 405: "Метод не поддерживается"}


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = _HTTP_MESSAGES.get(exc.status_code) or (
        exc.detail if isinstance(exc.detail, str) else "Ошибка запроса"
    )
    return _error_response(request, exc.status_code, "HTTP_ERROR", message)


# Custom pydantic error types raised by our validators -> business error codes.
_CUSTOM_CODES = {
    "currency_not_supported": "CURRENCY_NOT_SUPPORTED",
    "invalid_salary_range": "INVALID_SALARY_RANGE",
    "salary_required": "SALARY_REQUIRED",
}

_FIELD_MESSAGES = {
    "missing": "обязательное поле",
    "string_too_short": "слишком короткое значение (минимум {min_length})",
    "string_too_long": "слишком длинное значение (максимум {max_length})",
    "too_short": "слишком мало значений",
    "too_long": "слишком много значений (максимум {max_length})",
    "greater_than": "значение должно быть больше {gt}",
    "greater_than_equal": "значение должно быть не меньше {ge}",
    "less_than_equal": "значение должно быть не больше {le}",
    "literal_error": "недопустимое значение",
    "enum": "недопустимое значение",
    "int_parsing": "нужно целое число",
    "int_from_float": "нужно целое число",
    "uuid_parsing": "некорректный идентификатор",
    "bool_parsing": "нужно true или false",
    "json_invalid": "некорректный JSON",
}


def _field_name(loc: tuple[Any, ...]) -> str:
    parts = [str(p) for p in loc if p not in ("body", "query", "path")]
    return ".".join(parts) or "body"


def _field_message(err: dict[str, Any]) -> str:
    template = _FIELD_MESSAGES.get(err.get("type", ""))
    if template:
        try:
            return template.format(**(err.get("ctx") or {}))
        except (KeyError, IndexError):
            return template
    msg = str(err.get("msg", ""))
    if "valid email" in msg:
        return "некорректный email"
    return msg.removeprefix("Value error, ")


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Only field/message/type are returned: `input` would echo secrets such as passwords
    # back to the client, and `ctx` may hold exception objects that are not JSON-safe.
    errors = list(exc.errors())
    fields = [
        {
            "field": _field_name(tuple(e.get("loc", ()))),
            "message": _field_message(e),
            "type": e.get("type"),
        }
        for e in errors
    ]
    custom = next((e for e in errors if e.get("type") in _CUSTOM_CODES), None)
    if custom is not None:
        code, message = _CUSTOM_CODES[custom["type"]], str(custom.get("msg", ""))
    elif len(fields) == 1:
        code, message = "VALIDATION_ERROR", f"{fields[0]['field']}: {fields[0]['message']}"
    else:
        names = ", ".join(dict.fromkeys(f["field"] for f in fields))
        code, message = "VALIDATION_ERROR", f"Проверьте поля: {names}"
    return _error_response(request, 422, code, message, {"fields": fields})


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled_error",
        exc_info=exc,
        extra={"request_id": _request_id(request), "route": request.url.path},
    )
    return _error_response(request, 500, "INTERNAL_ERROR", "Внутренняя ошибка сервера")
