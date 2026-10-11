from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _BACKEND_ROOT / ".env"


def _strip_wrapping_quotes(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    return text


def _to_sqlalchemy_url(url: str, driver: str) -> str:
    """Accept Neon `postgresql://` URLs and rewrite for SQLAlchemy drivers.

    - async → `postgresql+asyncpg://...?ssl=require`
    - sync  → `postgresql+psycopg://...?sslmode=require`
    Drops `channel_binding` (breaks some serverless drivers).
    """
    text = _strip_wrapping_quotes(url)
    if text.startswith("postgres://"):
        text = "postgresql://" + text[len("postgres://") :]

    prefix = f"postgresql+{driver}://"
    if text.startswith(prefix):
        pass
    elif text.startswith("postgresql://"):
        text = prefix + text[len("postgresql://") :]
    else:
        return text

    parsed = urlparse(text)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.pop("channel_binding", None)
    if driver == "asyncpg":
        query.pop("sslmode", None)
        query.setdefault("ssl", "require")
    else:
        query.pop("ssl", None)
        query.setdefault("sslmode", "require")
    return urlunparse(parsed._replace(query=urlencode(query)))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "dev"
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    database_url: str = Field(..., alias="DATABASE_URL")
    database_url_sync: str = Field("", alias="DATABASE_URL_SYNC")
    # Neon console exposes this alongside the pooled DATABASE_URL; used when SYNC is unset.
    database_url_unpooled: str = Field("", alias="DATABASE_URL_UNPOOLED")
    jwt_secret: str = Field(..., alias="JWT_SECRET", min_length=32)
    # 8 hours: the frontend keeps the access token and has no refresh flow (Backend.md).
    jwt_access_ttl_min: int = Field(480, alias="JWT_ACCESS_TTL_MIN")
    jwt_refresh_ttl_days: int = Field(7, alias="JWT_REFRESH_TTL_DAYS")
    cors_origins: str = Field("http://localhost:5173", alias="CORS_ORIGINS")
    public_api_url: str = Field("http://localhost:8000", alias="PUBLIC_API_URL")
    # Frontend origin, used for Career Passport links.
    public_app_url: str = Field("http://localhost:5173", alias="PUBLIC_APP_URL")
    smtp_host: str = Field("", alias="SMTP_HOST")
    smtp_port: int = Field(587, alias="SMTP_PORT", ge=1, le=65535)
    smtp_username: str = Field("", alias="SMTP_USERNAME")
    smtp_password: str = Field("", alias="SMTP_PASSWORD")
    smtp_from_email: str = Field("no-reply@example.invalid", alias="SMTP_FROM_EMAIL")
    smtp_use_ssl: bool = Field(False, alias="SMTP_USE_SSL")
    smtp_starttls: bool = Field(True, alias="SMTP_STARTTLS")
    smtp_timeout_sec: int = Field(10, alias="SMTP_TIMEOUT_SEC", ge=1, le=60)
    fsp_provider: str = Field("mock", alias="FSP_PROVIDER")
    fsp_base_url: str = Field("", alias="FSP_BASE_URL")
    fsp_api_token: str = Field("", alias="FSP_API_TOKEN")
    fsp_timeout_sec: int = Field(2, alias="FSP_TIMEOUT_SEC")
    fsp_cache_ttl_hours: int = Field(24, alias="FSP_CACHE_TTL_HOURS")
    matcher_provider: str = Field("baseline", alias="MATCHER_PROVIDER")
    ml_matcher_url: str = Field("", alias="ML_MATCHER_URL")
    ml_timeout_sec: float = Field(2.0, alias="ML_TIMEOUT_SEC")
    pass_score: int = Field(70, alias="PASS_SCORE", ge=0, le=100)
    grade_cooldown_days: int = Field(90, alias="GRADE_COOLDOWN_DAYS", ge=0)
    test_attempt_ttl_min: int = Field(30, alias="TEST_ATTEMPT_TTL_MIN", ge=1)
    # After a failed attempt the same (or a higher) grade can be retried after this pause;
    # a lower grade stays available immediately.
    test_retry_cooldown_hours: int = Field(24, alias="TEST_RETRY_COOLDOWN_HOURS", ge=0)
    # A static question leaves rotation after this many shows (exposure control).
    static_item_max_exposures: int = Field(200, alias="STATIC_ITEM_MAX_EXPOSURES", ge=1)
    consent_version: str = Field("2026-10-01", alias="CONSENT_VERSION")
    rate_limit_enabled: bool = Field(True, alias="RATE_LIMIT_ENABLED")

    @model_validator(mode="before")
    @classmethod
    def normalize_database_urls(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        values = dict(data)

        async_raw = values.get("DATABASE_URL") or values.get("database_url")
        sync_raw = values.get("DATABASE_URL_SYNC") or values.get("database_url_sync")
        unpooled_raw = values.get("DATABASE_URL_UNPOOLED") or values.get(
            "database_url_unpooled"
        )

        if async_raw:
            values["DATABASE_URL"] = _to_sqlalchemy_url(str(async_raw), "asyncpg")

        if sync_raw:
            values["DATABASE_URL_SYNC"] = _to_sqlalchemy_url(str(sync_raw), "psycopg")
        elif unpooled_raw:
            values["DATABASE_URL_SYNC"] = _to_sqlalchemy_url(str(unpooled_raw), "psycopg")
        elif async_raw:
            values["DATABASE_URL_SYNC"] = _to_sqlalchemy_url(str(async_raw), "psycopg")

        return values

    @model_validator(mode="after")
    def require_sync_database_url(self) -> "Settings":
        if not self.database_url_sync:
            raise ValueError(
                "DATABASE_URL_SYNC is required (or set DATABASE_URL_UNPOOLED for Neon)"
            )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_dev(self) -> bool:
        return self.app_env.lower() in {"dev", "development", "local", "test"}


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
