from uuid import UUID

import jwt
from fastapi import APIRouter, Request, Response

from app.core.config import get_settings
from app.core.deps import CurrentUser, DbSession
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=not settings.is_dev,
        samesite="lax",
        max_age=settings.jwt_refresh_ttl_days * 24 * 3600,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")


@router.post("/register", response_model=RegisterResponse)
async def register(payload: RegisterRequest, db: DbSession) -> RegisterResponse:
    user, token = await auth_service.register_user(
        db, email=payload.email, password=payload.password, role=payload.role
    )
    return RegisterResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        email_verified=False,
        verification_required=True,
        verification_token=token if get_settings().is_dev else None,
    )


@router.post("/verify-email")
async def verify_email(payload: VerifyEmailRequest, db: DbSession) -> dict:
    await auth_service.verify_email(db, token=payload.token)
    return {"verified": True}


@router.post("/resend-verification")
async def resend_verification(payload: ResendVerificationRequest, db: DbSession) -> dict:
    token = await auth_service.resend_verification(db, email=payload.email)
    body: dict = {"accepted": True}
    if token:
        body["verification_token"] = token
    return body


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, request: Request, response: Response, db: DbSession
) -> TokenResponse:
    _user, access, expires_in, refresh = await auth_service.login_user(
        db,
        email=payload.email,
        password=payload.password,
        user_agent=request.headers.get("user-agent"),
    )
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access, expires_in=expires_in)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, db: DbSession) -> TokenResponse:
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise AppError("REFRESH_TOKEN_EXPIRED", "Refresh token missing", 401)
    _user, access, expires_in, refresh = await auth_service.refresh_session(
        db, refresh_token=token, user_agent=request.headers.get("user-agent")
    )
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access, expires_in=expires_in)


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response, db: DbSession, user: CurrentUser) -> None:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        try:
            payload = decode_access_token(auth.split(" ", 1)[1])
            await auth_service.logout_session(db, session_id=UUID(payload["sid"]))
        except jwt.PyJWTError:
            pass
    _clear_refresh_cookie(response)


@router.get("/me", response_model=MeResponse)
async def me(user: CurrentUser) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        email_verified=user.email_verified_at is not None,
    )
