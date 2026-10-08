from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.core.deps import DbSession
from app.integrations.fsp import get_fsp_adapter

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def live() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(db: DbSession) -> dict:
    settings = get_settings()
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "down"
    adapter = get_fsp_adapter()
    fsp_ok = await adapter.healthcheck()
    status = "ok" if db_status == "ok" else "degraded"
    return {
        "status": status,
        "database": db_status,
        "fsp_provider": settings.fsp_provider,
        "fsp_healthy": fsp_ok,
        "matcher": settings.matcher_provider or "baseline",
    }
