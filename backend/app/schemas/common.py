"""Shared API types. JSON is camelCase like frontend/src/entities/types.ts; Python is snake_case."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict
from pydantic.alias_generators import to_camel
from pydantic_core import PydanticCustomError

WorkFormatValue = Literal["remote", "hybrid", "office"]
ReadinessValue = Literal["actively_looking", "open_to_offers", "not_looking"]
GradeValue = Literal["intern", "junior", "middle", "senior", "lead"]


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


def _blank_to_none(value: object) -> object:
    """Forms send "" for untouched optional inputs; store that as "not set"."""
    if isinstance(value, str) and not value.strip():
        return None
    return value.strip() if isinstance(value, str) else value


def _zero_to_none(value: object) -> object:
    """Number inputs coerce an empty field to 0; a zero salary means "not set"."""
    return None if value in (0, "0", "") else value


def _rub_only(value: object) -> object:
    if value is not None and value != "RUB":
        # Mapped to code CURRENCY_NOT_SUPPORTED by the validation error handler.
        raise PydanticCustomError(
            "currency_not_supported", "Зарплатная вилка указывается только в рублях (RUB)"
        )
    return value


OptionalText = Annotated[str | None, BeforeValidator(_blank_to_none)]
OptionalSalary = Annotated[int | None, BeforeValidator(_zero_to_none)]
# The frontend type allows USD, ТЗ requires roubles: accept the field, reject other values.
Currency = Annotated[str, BeforeValidator(_rub_only)]


def check_salary_range(salary_from: int | None, salary_to: int | None) -> None:
    if salary_from is not None and salary_from <= 0:
        raise PydanticCustomError("salary_required", "Зарплата должна быть больше нуля")
    if salary_from is not None and salary_to is not None and salary_to < salary_from:
        raise PydanticCustomError("invalid_salary_range", "Верхняя граница зарплаты меньше нижней")


def reject_explicit_nulls(model: BaseModel, *fields: str) -> None:
    """PATCH helper: omitting a field keeps it, but null cannot clear a NOT NULL column."""
    for name in fields:
        if name in model.model_fields_set and getattr(model, name) is None:
            raise ValueError(f"{to_camel(name)} не может быть пустым")


class OkResponse(ApiModel):
    ok: bool = True


class MatchReason(ApiModel):
    code: str
    label: str
    # False marks a mismatch (e.g. salary above the range); the UI shows it as a minus.
    positive: bool
