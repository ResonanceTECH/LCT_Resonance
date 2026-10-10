"""Candidate-only collections (`/candidate/...`, singular, as in the frontend client)."""

from uuid import UUID

from fastapi import APIRouter

from app.core.deps import CandidateUser, DbSession
from app.schemas.offer import OfferOut
from app.schemas.vacancy import SavedResponse, VacancyOut
from app.services import offers, vacancies

router = APIRouter(prefix="/candidate", tags=["candidate"])


@router.get("/offers", response_model=list[OfferOut])
async def my_offers(db: DbSession, user: CandidateUser) -> list[OfferOut]:
    return await offers.list_for_candidate(db, user)


@router.get("/saved-vacancies", response_model=list[VacancyOut])
async def saved_vacancies(db: DbSession, user: CandidateUser) -> list[VacancyOut]:
    return await vacancies.saved_list(db, user)


@router.post("/saved-vacancies/{vacancy_id}", response_model=SavedResponse)
async def save_vacancy(vacancy_id: UUID, db: DbSession, user: CandidateUser) -> SavedResponse:
    return await vacancies.save(db, user, vacancy_id)


@router.delete("/saved-vacancies/{vacancy_id}", response_model=SavedResponse)
async def unsave_vacancy(vacancy_id: UUID, db: DbSession, user: CandidateUser) -> SavedResponse:
    return await vacancies.unsave(db, user, vacancy_id)
