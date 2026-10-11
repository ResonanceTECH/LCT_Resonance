from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from app.schemas.common import ApiModel

ConsentTypeValue = Literal["terms", "personal_data", "profile_publication", "fsp_sync"]


class ConsentOut(ApiModel):
    type: ConsentTypeValue
    accepted: bool
    # Version of the consent text that was accepted; compare with the current one to
    # ask for re-acceptance after the text changes.
    version: str | None = None
    current_version: str
    accepted_at: datetime | None = None
    withdrawn_at: datetime | None = None


class ConsentChange(ApiModel):
    type: ConsentTypeValue
    accepted: bool


class ConsentsUpdate(ApiModel):
    consents: list[ConsentChange] = Field(min_length=1, max_length=4)

    @field_validator("consents")
    @classmethod
    def _unique_types(cls, consents: list[ConsentChange]) -> list[ConsentChange]:
        if len({c.type for c in consents}) != len(consents):
            raise ValueError("each consent type can be listed once")
        return consents
