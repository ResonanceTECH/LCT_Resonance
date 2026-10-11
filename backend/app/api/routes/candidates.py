from uuid import UUID

from fastapi import APIRouter, Query

from app.core.deps import CandidateUser, CurrentUser, DbSession, EmployerOrAdmin, EmployerUser
from app.core.errors import AppError
from app.models.enums import UserRole
from app.schemas.candidate import (
    CandidateContacts,
    CandidateMeOut,
    CandidatePassport,
    CandidateProfileOut,
    CandidateUpdate,
    ProfileCompleteness,
    SkillRadar,
    TalentPoolResponse,
)
from app.schemas.common import GradeValue, ReadinessValue, WorkFormatValue
from app.schemas.consent import ConsentOut, ConsentsUpdate
from app.schemas.fsp import FspAchievementsResponse, FspLinkOut, FspLinkRequest
from app.services import candidate as candidate_service
from app.services import fsp as fsp_service
from app.services import insights, offers, passport, talent_pool

router = APIRouter(prefix="/candidates", tags=["candidates"])

# `/me...` routes are declared before `/{candidate_id}` so "me" is never parsed as an id.


@router.get("/me", response_model=CandidateMeOut)
async def get_me(db: DbSession, user: CandidateUser) -> CandidateMeOut:
    return await candidate_service.get_me(db, user)


@router.patch("/me", response_model=CandidateMeOut)
async def patch_me(payload: CandidateUpdate, db: DbSession, user: CandidateUser) -> CandidateMeOut:
    return await candidate_service.update_me(db, user, payload)


@router.delete("/me", status_code=204)
async def delete_me(db: DbSession, user: CandidateUser) -> None:
    await candidate_service.delete_account(db, user)


@router.get("/me/completeness", response_model=ProfileCompleteness)
async def get_completeness(db: DbSession, user: CandidateUser) -> ProfileCompleteness:
    return await candidate_service.get_completeness(db, user.id)


@router.get("/me/consents", response_model=list[ConsentOut])
async def get_consents(db: DbSession, user: CandidateUser) -> list[ConsentOut]:
    return await candidate_service.get_consents(db, user.id)


@router.put("/me/consents", response_model=list[ConsentOut])
async def put_consents(
    payload: ConsentsUpdate, db: DbSession, user: CandidateUser
) -> list[ConsentOut]:
    """Accept or withdraw: terms, personal_data, profile_publication, fsp_sync (152-ФЗ)."""
    return await candidate_service.update_consents(db, user.id, payload)


@router.get("/me/passport", response_model=CandidatePassport)
async def get_passport(db: DbSession, user: CandidateUser) -> CandidatePassport:
    """The public Career Passport link and, if strangers cannot open it yet, why."""
    return await passport.my_passport(db, user)


@router.get("/me/fsp/achievements", response_model=FspAchievementsResponse)
async def get_my_achievements(db: DbSession, user: CandidateUser) -> FspAchievementsResponse:
    return await fsp_service.achievements_response(db, user.id)


@router.post("/me/fsp/sync", response_model=FspAchievementsResponse)
async def sync_fsp(db: DbSession, user: CandidateUser) -> FspAchievementsResponse:
    """Without a link, the registry is searched by account email and full name."""
    return await fsp_service.sync_fsp(db, user=user)


@router.put("/me/fsp/link", response_model=FspLinkOut)
async def link_fsp(payload: FspLinkRequest, db: DbSession, user: CandidateUser) -> FspLinkOut:
    return await fsp_service.link_fsp(db, user_id=user.id, fsp_member_id=payload.fsp_member_id)


@router.delete("/me/fsp/link", status_code=204)
async def unlink_fsp(db: DbSession, user: CandidateUser) -> None:
    await fsp_service.unlink_fsp(db, user_id=user.id)


@router.get("", response_model=TalentPoolResponse)
async def talent_pool_search(
    db: DbSession,
    user: EmployerOrAdmin,
    specialization: str | None = None,
    grade: GradeValue | None = Query(default=None, description="Confirmed by a test"),
    skills: str | None = Query(default=None, description="Comma separated, all required"),
    work_format: WorkFormatValue | None = Query(default=None, alias="workFormat"),
    salary_from: int | None = Query(default=None, alias="salaryFrom", ge=0),
    salary_to: int | None = Query(default=None, alias="salaryTo", ge=0),
    fsp_discipline: str | None = Query(default=None, alias="fspDiscipline", max_length=255),
    has_fsp_achievements: bool | None = Query(default=None, alias="hasFspAchievements"),
    readiness: ReadinessValue | None = None,
    vacancy_id: UUID | None = Query(default=None, alias="vacancyId"),
    q: str | None = Query(default=None, max_length=128),
    sort: str | None = Query(default=None, pattern="^(match|grade|salary|name)?$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=talent_pool.MAX_LIMIT),
) -> TalentPoolResponse:
    """Talent Pool. With `vacancyId`: only the vacancy's tested category, ranked by match."""
    query = talent_pool.TalentPoolQuery(
        specialization=specialization,
        grade=grade,
        skills=skills,
        work_format=work_format,
        salary_from=salary_from,
        salary_to=salary_to,
        fsp_discipline=fsp_discipline,
        has_fsp_achievements=has_fsp_achievements,
        readiness=readiness,
        vacancy_id=vacancy_id,
        q=q,
        sort=sort,
        page=page,
        limit=limit,
    )
    return await talent_pool.search(db, query, viewer=user)


@router.get("/{candidate_id}", response_model=CandidateProfileOut)
async def get_candidate(
    candidate_id: UUID, db: DbSession, user: EmployerOrAdmin
) -> CandidateProfileOut:
    """Profile without contacts; opening it counts as a profile view."""
    return await candidate_service.get_for_employer(db, candidate_id, user)


@router.get("/{candidate_id}/contacts", response_model=CandidateContacts)
async def get_contacts(candidate_id: UUID, db: DbSession, user: EmployerUser) -> CandidateContacts:
    """Only after the candidate accepted this employer's offer or applied to its vacancy."""
    return await offers.candidate_contacts(db, candidate_id=candidate_id, employer=user)


@router.get("/{candidate_id}/fsp/achievements", response_model=FspAchievementsResponse)
async def get_candidate_achievements(
    candidate_id: UUID, db: DbSession, user: EmployerOrAdmin
) -> FspAchievementsResponse:
    await candidate_service.get_visible_profile(db, candidate_id)
    return await fsp_service.achievements_response(db, candidate_id)


@router.get("/{candidate_id}/skill-radar", response_model=SkillRadar)
async def get_skill_radar(candidate_id: UUID, db: DbSession, user: CurrentUser) -> SkillRadar:
    # Candidates see only their own radar; employers and admins see any visible candidate.
    if user.role == UserRole.candidate.value and user.id != candidate_id:
        raise AppError("CANDIDATE_NOT_FOUND", "Кандидат не найден", 404)
    return await insights.radar_for(db, candidate_id)
