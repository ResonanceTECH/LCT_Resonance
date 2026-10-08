from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(pattern="^(candidate|employer)$")


class RegisterResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    email_verified: bool
    verification_required: bool
    verification_token: str | None = None  # only in APP_ENV=dev


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MeResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    email_verified: bool
