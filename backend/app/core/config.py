from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "dev"
    database_url: str = Field(..., alias="DATABASE_URL")
    database_url_sync: str = Field(..., alias="DATABASE_URL_SYNC")
    jwt_secret: str = Field(..., alias="JWT_SECRET", min_length=32)
    jwt_access_ttl_min: int = Field(15, alias="JWT_ACCESS_TTL_MIN")
    jwt_refresh_ttl_days: int = Field(7, alias="JWT_REFRESH_TTL_DAYS")
    cors_origins: str = Field("http://localhost:5173", alias="CORS_ORIGINS")
    fsp_provider: str = Field("mock", alias="FSP_PROVIDER")
    fsp_base_url: str = Field("", alias="FSP_BASE_URL")
    fsp_api_token: str = Field("", alias="FSP_API_TOKEN")
    fsp_timeout_sec: int = Field(2, alias="FSP_TIMEOUT_SEC")
    fsp_cache_ttl_hours: int = Field(24, alias="FSP_CACHE_TTL_HOURS")
    matcher_provider: str = Field("baseline", alias="MATCHER_PROVIDER")
    ml_matcher_url: str = Field("", alias="ML_MATCHER_URL")
    pass_score: int = Field(70, alias="PASS_SCORE")
    grade_cooldown_days: int = Field(90, alias="GRADE_COOLDOWN_DAYS")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_dev(self) -> bool:
        return self.app_env.lower() in {"dev", "development", "local", "test"}


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
