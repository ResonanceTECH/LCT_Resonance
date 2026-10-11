from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import ApiModel

RoleValue = Literal["candidate", "employer", "admin"]


class RegisterRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["candidate", "employer"]
    display_name: str = Field(min_length=2, max_length=255)
    # Separate checkboxes (152-ФЗ): do not collapse terms + personal data into one.
    terms_accepted: bool
    personal_data_consent: bool
    # Optional: career passport visibility for candidates.
    public_passport_consent: bool = False

    @field_validator("terms_accepted")
    @classmethod
    def _require_terms(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Необходимо принять Условия использования")
        return value

    @field_validator("personal_data_consent")
    @classmethod
    def _require_personal_data(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Необходимо дать согласие на обработку персональных данных")
        return value


class LoginRequest(ApiModel):
    # Plain string on purpose: login must work for any stored address, and the
    # lookup is case-insensitive anyway. Format is enforced at registration.
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class AuthUserOut(ApiModel):
    id: UUID
    email: str
    role: RoleValue
    display_name: str
    # Extra to the frontend type: until verified, employers cannot send offers and
    # candidates are hidden from the Talent Pool.
    email_verified: bool


class AuthResponse(ApiModel):
    access_token: str
    user: AuthUserOut


class VerifyEmailRequest(ApiModel):
    token: str = Field(min_length=1, max_length=256)
