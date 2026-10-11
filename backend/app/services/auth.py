from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError, integrity_constraint_name
from app.core.security import (
    create_access_token,
    generate_token,
    hash_password_async,
    hash_token,
    verify_password_async,
)
from app.models.candidate import CandidateProfile
from app.models.enums import ProfileVisibility, Readiness, UserRole, UserStatus
from app.models.user import AuthSession, EmailVerificationToken, User
from app.schemas.auth import AuthUserOut
from app.schemas.consent import ConsentChange
from app.services import consents as consents_service
from app.services import taxonomy
from app.services.audit import write_audit

VERIFICATION_TOKEN_TTL = timedelta(days=2)
# A new candidate starts like in the frontend mocks until the profile is filled in.
DEFAULT_SPECIALIZATION = "Frontend"
DEFAULT_GRADE = "junior"


@dataclass(frozen=True)
class IssuedTokens:
    user: User
    access_token: str
    expires_in: int
    refresh_token: str


def _email_taken() -> AppError:
    return AppError("EMAIL_ALREADY_EXISTS", "Email уже зарегистрирован", 409)


def to_auth_user(user: User) -> AuthUserOut:
    return AuthUserOut(
        id=user.id,
        email=user.email,
        role=user.role,
        display_name=user.display_name,
        email_verified=user.email_verified_at is not None,
    )


async def _find_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(func.lower(User.email) == email.strip().lower()))
    return result.scalar_one_or_none()


def _new_verification_token(user_id: UUID) -> tuple[EmailVerificationToken, str]:
    raw = generate_token()
    row = EmailVerificationToken(
        user_id=user_id,
        token_hash=hash_token(raw),
        expires_at=datetime.now(UTC) + VERIFICATION_TOKEN_TTL,
    )
    return row, raw


async def start_session(db: AsyncSession, user: User, *, user_agent: str | None) -> IssuedTokens:
    """Open a refresh session and sign an access token bound to it (`sid`)."""
    refresh_raw = generate_token()
    session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_raw),
        expires_at=datetime.now(UTC) + timedelta(days=get_settings().jwt_refresh_ttl_days),
        user_agent=(user_agent or "")[:512] or None,
    )
    db.add(session)
    await db.commit()
    access, expires_in = create_access_token(user_id=user.id, role=user.role, session_id=session.id)
    return IssuedTokens(user, access, expires_in, refresh_raw)


async def register_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    role: str,
    display_name: str,
    terms_accepted: bool,
    personal_data_consent: bool,
    public_passport_consent: bool = False,
) -> tuple[User, str]:
    """Create the account (and a starter candidate profile); returns the raw verify token."""
    if await _find_user_by_email(db, email) is not None:
        raise _email_taken()

    user = User(
        email=email.strip().lower(),
        password_hash=await hash_password_async(password),
        display_name=display_name.strip(),
        role=role,
        status=UserStatus.active.value,
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError as exc:
        # A concurrent registration with the same email won the race.
        await db.rollback()
        if integrity_constraint_name(exc) == "ux_users_email":
            raise _email_taken() from exc
        raise

    if role == UserRole.candidate.value:
        spec = await taxonomy.specialization_by_name(db, DEFAULT_SPECIALIZATION)
        grade = await taxonomy.grade_by_code(db, DEFAULT_GRADE)
        db.add(
            CandidateProfile(
                user_id=user.id,
                full_name=user.display_name,
                declared_specialization_id=spec.id,
                declared_grade_id=grade.id,
                readiness=Readiness.open_to_offers.value,
                profile_visibility=(
                    ProfileVisibility.employers.value
                    if public_passport_consent
                    else ProfileVisibility.private.value
                ),
            )
        )

    consent_changes: list[ConsentChange] = []
    if terms_accepted:
        consent_changes.append(ConsentChange(type="terms", accepted=True))
    if personal_data_consent:
        consent_changes.append(ConsentChange(type="personal_data", accepted=True))
    if public_passport_consent and role == UserRole.candidate.value:
        consent_changes.append(ConsentChange(type="profile_publication", accepted=True))
    if consent_changes:
        await consents_service.apply_changes(db, user.id, consent_changes)

    token_row, raw_token = _new_verification_token(user.id)
    db.add(token_row)
    await write_audit(
        db,
        action="USER_REGISTERED",
        entity_type="user",
        entity_id=str(user.id),
        actor_user_id=user.id,
        metadata={
            "role": role,
            "public_passport_consent": public_passport_consent
            and role == UserRole.candidate.value,
        },
    )
    await db.commit()
    return user, raw_token


async def verify_email(db: AsyncSession, *, token: str) -> User:
    result = await db.execute(
        select(EmailVerificationToken)
        .where(EmailVerificationToken.token_hash == hash_token(token))
        .with_for_update()
    )
    row = result.scalar_one_or_none()
    if row is None or row.used_at is not None:
        raise AppError("INVALID_VERIFICATION_TOKEN", "Ссылка подтверждения недействительна", 400)
    if row.expires_at < datetime.now(UTC):
        raise AppError(
            "VERIFICATION_TOKEN_EXPIRED", "Срок действия ссылки истёк, запросите новую", 400
        )

    user = await db.get(User, row.user_id)
    if user is None:
        raise AppError("USER_NOT_FOUND", "Пользователь не найден", 404)

    now = datetime.now(UTC)
    row.used_at = now
    user.email_verified_at = user.email_verified_at or now
    await write_audit(
        db,
        action="EMAIL_VERIFIED",
        entity_type="user",
        entity_id=str(user.id),
        actor_user_id=user.id,
    )
    await db.commit()
    return user


async def resend_verification(db: AsyncSession, *, email: str) -> str | None:
    """New verify token, or None. The caller answers the same either way (no email probing)."""
    user = await _find_user_by_email(db, email)
    if user is None or user.email_verified_at is not None:
        return None
    token_row, raw_token = _new_verification_token(user.id)
    db.add(token_row)
    await db.commit()
    return raw_token


async def login_user(
    db: AsyncSession, *, email: str, password: str, user_agent: str | None
) -> IssuedTokens:
    user = await _find_user_by_email(db, email)
    # Always run the hash check so timing does not reveal whether the email exists.
    password_ok = await verify_password_async(password, user.password_hash if user else None)
    if user is None or not password_ok:
        raise AppError("INVALID_CREDENTIALS", "Неверный email или пароль", 401)
    if user.status != UserStatus.active.value:
        raise AppError("USER_BLOCKED", "Аккаунт заблокирован", 403)
    # An unverified email does not block login (Backend.md): it hides the candidate from
    # the Talent Pool and stops an employer from sending offers until confirmed.
    return await start_session(db, user, user_agent=user_agent)


async def _revoke_all_sessions(db: AsyncSession, user_id: UUID) -> None:
    await db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )


async def refresh_session(
    db: AsyncSession, *, refresh_token: str, user_agent: str | None
) -> IssuedTokens:
    """Rotate the refresh token: the presented session is revoked and a new one opened."""
    result = await db.execute(
        select(AuthSession)
        .where(AuthSession.refresh_token_hash == hash_token(refresh_token))
        .with_for_update()
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise AppError("REFRESH_TOKEN_INVALID", "Сессия недействительна, войдите снова", 401)
    if session.revoked_at is not None:
        # A rotated-out token came back: assume it was stolen and end every session.
        await _revoke_all_sessions(db, session.user_id)
        await db.commit()
        raise AppError("REFRESH_TOKEN_REUSED", "Сессия завершена, войдите снова", 401)
    if session.expires_at <= datetime.now(UTC):
        raise AppError("REFRESH_TOKEN_EXPIRED", "Сессия истекла, войдите снова", 401)

    user = await db.get(User, session.user_id)
    if user is None or user.status != UserStatus.active.value:
        raise AppError("UNAUTHORIZED", "Аккаунт недоступен", 401)

    session.revoked_at = datetime.now(UTC)
    return await start_session(db, user, user_agent=user_agent)


async def logout_session(db: AsyncSession, *, session_id: UUID) -> None:
    session = await db.get(AuthSession, session_id)
    if session and session.revoked_at is None:
        session.revoked_at = datetime.now(UTC)
        await db.commit()
