from fastapi import APIRouter

from app.api.v1 import auth, candidates, companies, matching, offers, taxonomy, tests, vacancies

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(taxonomy.router)
api_router.include_router(candidates.router)
api_router.include_router(tests.router)
api_router.include_router(companies.router)
api_router.include_router(vacancies.router)
api_router.include_router(matching.router)
api_router.include_router(offers.router)
