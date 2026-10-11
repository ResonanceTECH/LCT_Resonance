from app.core.config import Settings, _to_sqlalchemy_url


def test_neon_pooled_url_becomes_asyncpg() -> None:
    raw = (
        '"postgresql://u:p@ep-x-pooler.aws.neon.tech/neondb'
        '?channel_binding=require&sslmode=require"'
    )
    out = _to_sqlalchemy_url(raw, "asyncpg")
    assert out.startswith("postgresql+asyncpg://")
    assert "ssl=require" in out
    assert "sslmode" not in out
    assert "channel_binding" not in out


def test_neon_unpooled_url_becomes_psycopg() -> None:
    raw = "postgresql://u:p@ep-x.aws.neon.tech/neondb?sslmode=require"
    out = _to_sqlalchemy_url(raw, "psycopg")
    assert out.startswith("postgresql+psycopg://")
    assert "sslmode=require" in out


def test_settings_maps_unpooled_to_sync() -> None:
    settings = Settings(
        database_url="postgresql://u:p@ep-x-pooler.aws.neon.tech/neondb?sslmode=require",
        database_url_sync="",
        database_url_unpooled="postgresql://u:p@ep-x.aws.neon.tech/neondb?sslmode=require",
        jwt_secret="x" * 32,
    )
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.database_url_sync.startswith("postgresql+psycopg://")
    assert "ep-x.aws.neon.tech" in settings.database_url_sync
