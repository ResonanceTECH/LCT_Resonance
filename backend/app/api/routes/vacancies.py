from uuid import UUID

from fastapi import APIRouter, Query

from app.core.deps import CandidateUser, CurrentUser, DbSession, EmployerOrAdmin
from app.schemas.candidate import CandidateMatch, TalentPoolResponse
from app.schemas.vacancy import (
    ApplyResponse,
    VacancyOut,
    VacancyParseRequest,
    VacancyParseResult,
    VacancyUpdate,
    VacancyWithMatch,
)
from app.services import talent_pool, vacancies, vacancy_parser

router = APIRouter(prefix="/vacancies", tags=["vacancies"])


@router.get("", response_model=list[VacancyWithMatch])
async def catalog(
    db: DbSession,
    user: CurrentUser,
    specialization: str | None = None,
    match_to_me: bool = Query(default=False, alias="matchToMe"),
    saved_only: bool = Query(default=False, alias="savedOnly"),
) -> list[VacancyWithMatch]:
    """Active vacancies. Candidates also get `saved`, `applied` and, on request, `match`."""
    return await vacancies.catalog(
        db, user=user, specialization=specialization, match_to_me=match_to_me, saved_only=saved_only
    )


@router.post("/parse", response_model=VacancyParseResult)
async def parse_vacancy(
    payload: VacancyParseRequest, db: DbSession, user: EmployerOrAdmin
) -> VacancyParseResult:
    """Draft from free text for the vacancy form; the employer reviews it before saving."""
    return await vacancy_parser.parse(db, payload.text)


@router.get("/{vacancy_id}", response_model=VacancyOut)
async def get_vacancy(vacancy_id: UUID, db: DbSession, user: CurrentUser) -> VacancyOut:
    return await vacancies.get_vacancy(db, vacancy_id, user)


@router.patch("/{vacancy_id}", response_model=VacancyOut)
async def patch_vacancy(
    vacancy_id: UUID, payload: VacancyUpdate, db: DbSession, user: EmployerOrAdmin
) -> VacancyOut:
    """Owner only; closing or archiving is a status change (there is no delete)."""
    return await vacancies.update_vacancy(db, vacancy_id=vacancy_id, user=user, payload=payload)


@router.get("/{vacancy_id}/match-to-me", response_model=CandidateMatch)
async def match_to_me(vacancy_id: UUID, db: DbSession, user: CandidateUser) -> CandidateMatch:
    return await vacancies.match_to_me(db, user, vacancy_id)


@router.post("/{vacancy_id}/apply", response_model=ApplyResponse)
async def apply(vacancy_id: UUID, db: DbSession, user: CandidateUser) -> ApplyResponse:
    """A candidate's own response; the employer then may see the contacts (ТЗ)."""
    return await vacancies.apply(db, user, vacancy_id)


@router.get("/{vacancy_id}/matches", response_model=TalentPoolResponse)
async def vacancy_matches(
    vacancy_id: UUID,
    db: DbSession,
    user: EmployerOrAdmin,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=talent_pool.MAX_LIMIT),
) -> TalentPoolResponse:
    """Shortcut for `GET /candidates?vacancyId=`."""
    query = talent_pool.TalentPoolQuery(vacancy_id=vacancy_id, page=page, limit=limit)
    return await talent_pool.search(db, query, viewer=user)
