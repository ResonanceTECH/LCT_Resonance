from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import create_access_token, decode_access_token


def test_jwt_expiration_and_payload():
    get_settings.cache_clear()
    settings = get_settings()
    uid, sid = uuid4(), uuid4()
    token, ttl = create_access_token(user_id=uid, role="candidate", session_id=sid)
    assert ttl == settings.jwt_access_ttl_min * 60
    payload = decode_access_token(token)
    assert payload["sub"] == str(uid)
    assert payload["role"] == "candidate"
    assert payload["sid"] == str(sid)
    assert "email" not in payload

    expired = jwt.encode(
        {
            "sub": str(uid),
            "role": "candidate",
            "sid": str(sid),
            "exp": int((datetime.now(UTC) - timedelta(minutes=1)).timestamp()),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired)
