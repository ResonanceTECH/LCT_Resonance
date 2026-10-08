from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.deps import DbSession, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.offer import CandidateContactOut, OfferCreate, OfferOut
from app.services import offers as offers_service

router = APIRouter(prefix="/offers", tags=["offers"])


@router.post("", response_model=OfferOut, status_code=201)
async def create_offer(
    payload: OfferCreate,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer)),
) -> OfferOut:
    return await offers_service.create_offer(db, employer_id=user.id, payload=payload)


@router.get("", response_model=list[OfferOut])
async def list_offers(db: DbSession, user: User = Depends(require_roles(
    UserRole.employer, UserRole.candidate, UserRole.admin
))) -> list[OfferOut]:
    return await offers_service.list_offers(db, user=user)


@router.get("/{offer_id}", response_model=OfferOut)
async def get_offer(
    offer_id: UUID,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer, UserRole.candidate, UserRole.admin)),
) -> OfferOut:
    offer, company = await offers_service.get_offer_for_participant(
        db, offer_id=offer_id, user=user
    )
    return offers_service.to_out(offer, company)


@router.post("/{offer_id}/view", response_model=OfferOut)
async def view_offer(
    offer_id: UUID,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.candidate)),
) -> OfferOut:
    return await offers_service.view_offer(db, offer_id=offer_id, candidate_id=user.id)


@router.post("/{offer_id}/accept", response_model=OfferOut)
async def accept_offer(
    offer_id: UUID,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.candidate)),
) -> OfferOut:
    return await offers_service.accept_offer(db, offer_id=offer_id, candidate_id=user.id)


@router.post("/{offer_id}/reject", response_model=OfferOut)
async def reject_offer(
    offer_id: UUID,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.candidate)),
) -> OfferOut:
    return await offers_service.reject_offer(db, offer_id=offer_id, candidate_id=user.id)


@router.post("/{offer_id}/withdraw", response_model=OfferOut)
async def withdraw_offer(
    offer_id: UUID,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer)),
) -> OfferOut:
    return await offers_service.withdraw_offer(db, offer_id=offer_id, employer_id=user.id)


@router.get("/{offer_id}/candidate-contact", response_model=CandidateContactOut)
async def candidate_contact(
    offer_id: UUID,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer)),
) -> CandidateContactOut:
    return await offers_service.candidate_contact(db, offer_id=offer_id, employer_id=user.id)
