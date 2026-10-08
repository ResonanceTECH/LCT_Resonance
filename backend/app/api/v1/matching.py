from fastapi import APIRouter, Depends

from app.core.deps import DbSession, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.matching import MatchingSearchRequest, MatchingSearchResponse
from app.services import matching as matching_service

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/search", response_model=MatchingSearchResponse)
async def matching_search(
    payload: MatchingSearchRequest,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer, UserRole.admin)),
) -> MatchingSearchResponse:
    return await matching_service.search_matches(db, employer_id=user.id, payload=payload)
