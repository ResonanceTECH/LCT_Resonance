import logging

from fastapi import APIRouter, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.deps import DbSession
from app.integrations.fsp import get_fsp_adapter

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger("app.health")


@router.get("/live")
async def live() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def ready(db: DbSession, response: Response) -> dict:
    """503 only when the database is down: FSP outages are served from cache, not fatal."""
    settings = get_settings()
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except (SQLAlchemyError, OSError):
        logger.exception("readiness_db_check_failed")
        db_status = "down"
        response.status_code = 503
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "fspProvider": settings.fsp_provider,
        "fspHealthy": await get_fsp_adapter().healthcheck(),
        "matcher": settings.matcher_provider or "baseline",
    }
