from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import (
    create_access_token,
    generate_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.candidate import CandidateProfile
from app.models.enums import UserRole, UserStatus
from app.models.user import AuthSession, EmailVerificationToken, User
from app.services.audit import write_audit


async def register_user(
    db: AsyncSession, *, email: str, password: str, role: str
) -> tuple[User, str]:
    existing = await db.execute(
        select(User).where(func.lower(User.email) == email.lower())
    )
    if existing.scalar_one_or_none():
        raise AppError("EMAIL_ALREADY_EXISTS", "Email already registered", 409)

    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        role=role,
        status=UserStatus.active.value,
    )
    db.add(user)
    await db.flush()

    if role == UserRole.candidate.value:
        db.add(CandidateProfile(user_id=user.id))

    raw_token = generate_token()
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(days=2),
        )
    )
    await write_audit(
        db,
        action="USER_REGISTERED",
        entity_type="user",
        entity_id=str(user.id),
        actor_user_id=user.id,
        metadata={"role": role},
    )
    await db.commit()
    await db.refresh(user)
    return user, raw_token


async def verify_email(db: AsyncSession, *, token: str) -> User:
    token_hash = hash_token(token)
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )
    )
    row = result.scalar_one_or_none()
    if row is None or row.used_at is not None:
        raise AppError("INVALID_VERIFICATION_TOKEN", "Invalid verification token", 400)
    if row.expires_at < datetime.now(UTC):
        raise AppError("VERIFICATION_TOKEN_EXPIRED", "Verification token expired", 400)

    user = await db.get(User, row.user_id)
    if user is None:
        raise AppError("USER_NOT_FOUND", "User not found", 404)

    row.used_at = datetime.now(UTC)
    user.email_verified_at = datetime.now(UTC)
    await write_audit(
        db,
        action="EMAIL_VERIFIED",
        entity_type="user",
        entity_id=str(user.id),
        actor_user_id=user.id,
    )
    await db.commit()
    await db.refresh(user)
    return user


async def resend_verification(db: AsyncSession, *, email: str) -> str | None:
    result = await db.execute(select(User).where(func.lower(User.email) == email.lower()))
    user = result.scalar_one_or_none()
    # Do not leak existence
    if user is None or user.email_verified_at is not None:
        return None
    raw_token = generate_token()
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(days=2),
        )
    )
    await db.commit()
    return raw_token if get_settings().is_dev else None


async def login_user(
    db: AsyncSession, *, email: str, password: str, user_agent: str | None
) -> tuple[User, str, int, str]:
    result = await db.execute(select(User).where(func.lower(User.email) == email.lower()))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "Invalid email or password", 401)
    if user.status != UserStatus.active.value:
        raise AppError("USER_BLOCKED", "User is not active", 403)
    if user.email_verified_at is None:
        raise AppError("EMAIL_NOT_VERIFIED", "Email is not verified", 403)

    settings = get_settings()
    refresh_raw = generate_token()
    session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_raw),
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_ttl_days),
        user_agent=user_agent,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    access, expires_in = create_access_token(
        user_id=user.id, role=user.role, session_id=session.id
    )
    return user, access, expires_in, refresh_raw


async def refresh_session(
    db: AsyncSession, *, refresh_token: str, user_agent: str | None
) -> tuple[User, str, int, str]:
    token_hash = hash_token(refresh_token)
    result = await db.execute(
        select(AuthSession).where(AuthSession.refresh_token_hash == token_hash)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise AppError("REFRESH_TOKEN_REUSED", "Refresh token invalid or reused", 401)
    if session.revoked_at is not None:
        raise AppError("REFRESH_TOKEN_REUSED", "Refresh token invalid or reused", 401)
    if session.expires_at < datetime.now(UTC):
        raise AppError("REFRESH_TOKEN_EXPIRED", "Refresh token expired", 401)

    user = await db.get(User, session.user_id)
    if user is None or user.status != UserStatus.active.value:
        raise AppError("UNAUTHORIZED", "User inactive", 401)

    # rotate
    session.revoked_at = datetime.now(UTC)
    new_refresh = generate_token()
    new_session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_token(new_refresh),
        expires_at=datetime.now(UTC) + timedelta(days=get_settings().jwt_refresh_ttl_days),
        user_agent=user_agent,
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    access, expires_in = create_access_token(
        user_id=user.id, role=user.role, session_id=new_session.id
    )
    return user, access, expires_in, new_refresh


async def logout_session(db: AsyncSession, *, session_id: UUID) -> None:
    session = await db.get(AuthSession, session_id)
    if session and session.revoked_at is None:
        session.revoked_at = datetime.now(UTC)
        await db.commit()
