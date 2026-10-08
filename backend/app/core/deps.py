from __future__ import annotations

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
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
        raise AppError("UNAUTHORIZED", "Authentication required", 401)
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError as exc:
        raise AppError("ACCESS_TOKEN_EXPIRED", "Access token expired", 401) from exc
    except jwt.PyJWTError as exc:
        raise AppError("INVALID_TOKEN", "Invalid access token", 401) from exc

    user_id = UUID(payload["sub"])
    session_id = UUID(payload["sid"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or user.status != UserStatus.active.value:
        raise AppError("UNAUTHORIZED", "User not found or inactive", 401)

    session = await db.get(AuthSession, session_id)
    if session is None or session.revoked_at is not None or session.user_id != user.id:
        raise AppError("SESSION_REVOKED", "Session is not active", 401)

    request.state.user_id = str(user.id)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole | str):
    allowed = {r.value if isinstance(r, UserRole) else r for r in roles}

    async def _checker(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise AppError("FORBIDDEN_ROLE", "Insufficient role", 403)
        return user

    return _checker
