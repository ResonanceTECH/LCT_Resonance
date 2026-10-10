from uuid import UUID

from fastapi import APIRouter, Query

from app.core.deps import DbSession, EmployerOrAdmin, EmployerUser
from app.schemas.candidate import CandidateCompareResponse, CandidateProfileOut, ShortlistAdd
from app.schemas.common import OkResponse
from app.schemas.engagement import CompanyIn, CompanyOut
from app.schemas.offer import OfferOut
from app.schemas.vacancy import VacancyCreate, VacancyOut
from app.services import companies, insights, offers, shortlist, vacancies

router = APIRouter(prefix="/employer", tags=["employer"])


@router.get("/vacancies", response_model=list[VacancyOut])
async def my_vacancies(db: DbSession, user: EmployerOrAdmin) -> list[VacancyOut]:
    return await vacancies.list_owned(db, user)


@router.post("/vacancies", response_model=VacancyOut, status_code=201)
async def create_vacancy(
    payload: VacancyCreate, db: DbSession, user: EmployerOrAdmin
) -> VacancyOut:
    """The status comes from the form; a draft is already enough for matching."""
    return await vacancies.create_vacancy(db, user=user, payload=payload)


@router.get("/offers", response_model=list[OfferOut])
async def my_offers(db: DbSession, user: EmployerUser) -> list[OfferOut]:
    return await offers.list_for_employer(db, user)


@router.get("/shortlist", response_model=list[CandidateProfileOut])
async def get_shortlist(db: DbSession, user: EmployerUser) -> list[CandidateProfileOut]:
    return await shortlist.list_shortlist(db, user)


@router.post("/shortlist", response_model=OkResponse)
async def add_to_shortlist(payload: ShortlistAdd, db: DbSession, user: EmployerUser) -> OkResponse:
    await shortlist.add(db, user, payload.candidate_id)
    return OkResponse()


@router.delete("/shortlist/{candidate_id}", status_code=204)
async def remove_from_shortlist(candidate_id: UUID, db: DbSession, user: EmployerUser) -> None:
    await shortlist.remove(db, user, candidate_id)


@router.get("/candidates/compare", response_model=CandidateCompareResponse)
async def compare_candidates(
    db: DbSession,
    user: EmployerOrAdmin,
    ids: str = Query(description="Comma separated candidate ids, 2 to 4"),
) -> CandidateCompareResponse:
    return await insights.compare(db, ids)


@router.get("/company", response_model=CompanyOut)
async def get_company(db: DbSession, user: EmployerUser) -> CompanyOut:
    return await companies.get_company(db, user)


@router.put("/company", response_model=CompanyOut)
async def put_company(payload: CompanyIn, db: DbSession, user: EmployerUser) -> CompanyOut:
    """Create or update the company profile (description, industry, contacts)."""
    return await companies.upsert_company(db, user, payload)
