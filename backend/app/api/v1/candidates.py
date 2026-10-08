from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, DbSession, require_roles
from app.core.errors import AppError
from app.models.enums import UserRole, UserStatus
from app.models.user import User
from app.schemas.candidate import (
    CandidateMeResponse,
    CandidatePublicResponse,
    CandidateSkillIn,
    CandidateUpdate,
)
from app.schemas.common import Page
from app.schemas.fsp import FspAchievementOut, FspLinkRequest, FspSyncResponse
from app.services import candidate as candidate_service
from app.services import fsp as fsp_service

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("/me", response_model=CandidateMeResponse)
async def get_me(
    db: DbSession,
    user: User = Depends(require_roles(UserRole.candidate)),
) -> CandidateMeResponse:
    profile = await candidate_service.get_profile(db, user.id)
    return await candidate_service.to_me_response(db, profile)


@router.patch("/me", response_model=CandidateMeResponse)
async def patch_me(
    payload: CandidateUpdate,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.candidate)),
) -> CandidateMeResponse:
    return await candidate_service.update_profile(db, user.id, payload)


@router.delete("/me", status_code=204)
async def delete_me(
    db: DbSession,
    user: User = Depends(require_roles(UserRole.candidate)),
) -> None:
    user.status = UserStatus.deleted.value
    await db.commit()


@router.put("/me/skills", response_model=CandidateMeResponse)
async def put_skills(
    skills: list[CandidateSkillIn],
    db: DbSession,
    user: User = Depends(require_roles(UserRole.candidate)),
) -> CandidateMeResponse:
    return await candidate_service.replace_skills(db, user.id, skills)


@router.put("/me/fsp-link")
async def put_fsp_link(
    payload: FspLinkRequest,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.candidate)),
) -> dict:
    link = await fsp_service.link_fsp(db, user_id=user.id, fsp_member_id=payload.fsp_member_id)
    return {"fsp_member_id": link.fsp_member_id}


@router.delete("/me/fsp-link", status_code=204)
async def delete_fsp_link(
    db: DbSession,
    user: User = Depends(require_roles(UserRole.candidate)),
) -> None:
    await fsp_service.unlink_fsp(db, user_id=user.id)


@router.post("/me/fsp-sync", response_model=FspSyncResponse)
async def post_fsp_sync(
    db: DbSession,
    user: User = Depends(require_roles(UserRole.candidate)),
) -> FspSyncResponse:
    return await fsp_service.sync_fsp(db, user_id=user.id)


@router.get("/me/fsp-achievements", response_model=list[FspAchievementOut])
async def get_my_achievements(
    db: DbSession,
    user: User = Depends(require_roles(UserRole.candidate)),
) -> list[FspAchievementOut]:
    return await fsp_service._achievements_out(db, user.id)


@router.get("", response_model=Page[CandidatePublicResponse])
async def list_candidates(
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer, UserRole.admin)),
    specialization_id: UUID | None = None,
    grade_id: UUID | None = None,
    open_to_offers: bool | None = True,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
) -> Page[CandidatePublicResponse]:
    return await candidate_service.list_candidates(
        db,
        specialization_id=specialization_id,
        grade_id=grade_id,
        open_to_offers=open_to_offers,
        limit=limit,
        offset=offset,
    )


@router.get("/{candidate_id}", response_model=CandidatePublicResponse)
async def get_candidate(
    candidate_id: UUID,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer, UserRole.admin)),
) -> CandidatePublicResponse:
    profile = await candidate_service.get_profile(db, candidate_id)
    return await candidate_service.to_public_response(db, profile)


@router.get("/{candidate_id}/achievements", response_model=list[FspAchievementOut])
async def get_candidate_achievements(
    candidate_id: UUID,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer, UserRole.admin)),
) -> list[FspAchievementOut]:
    return await fsp_service._achievements_out(db, candidate_id)
