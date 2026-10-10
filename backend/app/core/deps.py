from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole, UserStatus
from app.models.user import AuthSession, User

bearer_scheme = HTTPBearer(auto_error=False)
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    request: Request,
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise AppError("UNAUTHORIZED", "Требуется авторизация", 401)
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
        session_id = UUID(payload["sid"])
    except jwt.ExpiredSignatureError as exc:
        raise AppError("TOKEN_EXPIRED", "Сессия истекла, войдите снова", 401) from exc
    except (jwt.PyJWTError, ValueError) as exc:
        raise AppError("INVALID_TOKEN", "Требуется авторизация", 401) from exc

    user = await db.get(User, user_id)
    if user is None or user.status != UserStatus.active.value:
        raise AppError("UNAUTHORIZED", "Аккаунт недоступен", 401)

    session = await db.get(AuthSession, session_id)
    if (
        session is None
        or session.revoked_at is not None
        or session.expires_at <= datetime.now(UTC)
        or session.user_id != user.id
    ):
        raise AppError("TOKEN_EXPIRED", "Сессия завершена, войдите снова", 401)

    request.state.user_id = str(user.id)
    request.state.session_id = session.id
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    allowed = {role.value for role in roles}

    async def _checker(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise AppError("FORBIDDEN_ROLE", "Недостаточно прав для этого действия", 403)
        return user

    return _checker


# Role-scoped aliases keep route signatures short: `user: CandidateUser`.
CandidateUser = Annotated[User, Depends(require_roles(UserRole.candidate))]
EmployerUser = Annotated[User, Depends(require_roles(UserRole.employer))]
EmployerOrAdmin = Annotated[User, Depends(require_roles(UserRole.employer, UserRole.admin))]
AdminUser = Annotated[User, Depends(require_roles(UserRole.admin))]
