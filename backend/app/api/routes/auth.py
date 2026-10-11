import contextlib
import html

from fastapi import APIRouter, Form, Query, Request, Response
from fastapi.responses import HTMLResponse

from app.core.config import get_settings
from app.core.deps import CurrentUser, DbSession
from app.core.errors import AppError
from app.core.rate_limit import LoginLimit, RegisterLimit, ResendVerificationLimit
from app.integrations.email import ensure_email_delivery_available, send_verification_email
from app.schemas.auth import (
    AuthResponse,
    AuthUserOut,
    LoginRequest,
    RegisterRequest,
    VerifyEmailRequest,
)
from app.schemas.common import OkResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

# Public path of this router; the refresh cookie is scoped to it.
AUTH_PATH = "/api/auth"
REFRESH_COOKIE = "refresh_token"


def _auth_response(response: Response, tokens: auth_service.IssuedTokens) -> AuthResponse:
    settings = get_settings()
    # The frontend keeps the access token; the HttpOnly refresh cookie enables /auth/refresh.
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=tokens.refresh_token,
        httponly=True,
        secure=not settings.is_dev,
        samesite="lax",
        max_age=settings.jwt_refresh_ttl_days * 24 * 3600,
        path=AUTH_PATH,
    )
    return AuthResponse(
        access_token=tokens.access_token, user=auth_service.to_auth_user(tokens.user)
    )


async def _send_verification_after_register(email: str, token: str) -> None:
    """A mail outage must not undo the registration: the link can be re-sent later.

    The failure itself is logged by the email integration.
    """
    with contextlib.suppress(AppError):
        await send_verification_email(email=email, token=token)


def _html_page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        "<!doctype html><html lang='ru'><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{title}</title><body><main>{body}</main></body></html>"
    )


@router.post("/register", response_model=AuthResponse, dependencies=[RegisterLimit])
async def register(
    payload: RegisterRequest, request: Request, response: Response, db: DbSession
) -> AuthResponse:
    """Creates the account and signs it in at once, like the frontend expects."""
    ensure_email_delivery_available()
    user, token = await auth_service.register_user(
        db,
        email=payload.email,
        password=payload.password,
        role=payload.role,
        display_name=payload.display_name,
        terms_accepted=payload.terms_accepted,
        personal_data_consent=payload.personal_data_consent,
        public_passport_consent=payload.public_passport_consent,
    )
    await _send_verification_after_register(user.email, token)
    if get_settings().is_dev:
        # Dev only: lets demos and tests confirm the email without a mailbox.
        response.headers["X-Verification-Token"] = token
    tokens = await auth_service.start_session(
        db, user, user_agent=request.headers.get("user-agent")
    )
    return _auth_response(response, tokens)


@router.post("/login", response_model=AuthResponse, dependencies=[LoginLimit])
async def login(
    payload: LoginRequest, request: Request, response: Response, db: DbSession
) -> AuthResponse:
    tokens = await auth_service.login_user(
        db,
        email=payload.email,
        password=payload.password,
        user_agent=request.headers.get("user-agent"),
    )
    return _auth_response(response, tokens)


@router.post("/refresh", response_model=AuthResponse)
async def refresh(request: Request, response: Response, db: DbSession) -> AuthResponse:
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise AppError("REFRESH_TOKEN_EXPIRED", "Сессия истекла, войдите снова", 401)
    tokens = await auth_service.refresh_session(
        db, refresh_token=token, user_agent=request.headers.get("user-agent")
    )
    return _auth_response(response, tokens)


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response, db: DbSession, user: CurrentUser) -> None:
    # `get_current_user` has already validated the token and stored its session id.
    await auth_service.logout_session(db, session_id=request.state.session_id)
    response.delete_cookie(REFRESH_COOKIE, path=AUTH_PATH)


@router.get("/me", response_model=AuthUserOut)
async def me(user: CurrentUser) -> AuthUserOut:
    return auth_service.to_auth_user(user)


@router.post("/verify-email", response_model=OkResponse)
async def verify_email(payload: VerifyEmailRequest, db: DbSession) -> OkResponse:
    await auth_service.verify_email(db, token=payload.token)
    return OkResponse()


@router.post(
    "/resend-verification", response_model=OkResponse, dependencies=[ResendVerificationLimit]
)
async def resend_verification(response: Response, db: DbSession, user: CurrentUser) -> OkResponse:
    ensure_email_delivery_available()
    token = await auth_service.resend_verification(db, email=user.email)
    if token:
        # Unlike registration, a failure here is reported: the user explicitly asked for
        # the letter and would otherwise see "sent" for an email that never left.
        await send_verification_email(email=user.email, token=token)
        if get_settings().is_dev:
            response.headers["X-Verification-Token"] = token
    return OkResponse()


@router.get("/verify-email/confirm", response_class=HTMLResponse, include_in_schema=False)
async def verification_confirmation_page(
    token: str = Query(min_length=32, max_length=256),
) -> HTMLResponse:
    # The link from the email opens this page; confirming takes an explicit POST so that
    # mail scanners prefetching the link do not verify the address on their own.
    safe_token = html.escape(token, quote=True)
    return _html_page(
        "Подтверждение почты",
        "<h1>Подтвердите почту</h1>"
        "<p>Нажмите кнопку, чтобы завершить подтверждение адреса.</p>"
        f"<form method='post' action='{AUTH_PATH}/verify-email/confirm'>"
        f"<input type='hidden' name='token' value='{safe_token}'>"
        "<button type='submit'>Подтвердить адрес</button></form>",
    )


@router.post("/verify-email/confirm", response_class=HTMLResponse, include_in_schema=False)
async def confirm_email_from_link(
    db: DbSession,
    token: str = Form(min_length=32, max_length=256),
) -> HTMLResponse:
    await auth_service.verify_email(db, token=token)
    app_url = html.escape(get_settings().public_app_url, quote=True)
    return _html_page(
        "Почта подтверждена",
        f"<h1>Адрес подтверждён</h1><p><a href='{app_url}/login'>Вернуться в Resonance</a></p>",
    )
