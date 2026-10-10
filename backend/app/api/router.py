"""All endpoints live under /api: the frontend's default `apiBaseUrl` (Backend.md)."""

from fastapi import APIRouter

from app.api.routes import (
    auth,
    candidate,
    candidates,
    employer,
    engagement,
    health,
    offers,
    taxonomy,
    tests,
    vacancies,
)

api_router = APIRouter()
for module_router in (
    health.router,
    auth.router,
    taxonomy.router,
    candidates.router,
    candidate.router,
    employer.router,
    vacancies.router,
    offers.router,
    tests.router,
    engagement.notifications_router,
    engagement.dashboard_router,
    engagement.admin_router,
    engagement.public_router,
):
    api_router.include_router(module_router)
