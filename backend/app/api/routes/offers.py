from uuid import UUID

from fastapi import APIRouter

from app.core.deps import CandidateUser, CurrentUser, DbSession, EmployerUser
from app.core.rate_limit import OffersPerDayLimit
from app.schemas.offer import OfferCreate, OfferOut
from app.services import offers

router = APIRouter(prefix="/offers", tags=["offers"])


@router.post("", response_model=OfferOut, status_code=201, dependencies=[OffersPerDayLimit])
async def create_offer(payload: OfferCreate, db: DbSession, user: EmployerUser) -> OfferOut:
    """Requires a verified employer email; the salary range in RUB is mandatory."""
    return await offers.create_offer(db, employer=user, payload=payload)


@router.get("/{offer_id}", response_model=OfferOut)
async def get_offer(offer_id: UUID, db: DbSession, user: CurrentUser) -> OfferOut:
    """Participants only; the candidate's first opening marks the offer as viewed."""
    return await offers.get_offer(db, offer_id=offer_id, user=user)


@router.post("/{offer_id}/accept", response_model=OfferOut)
async def accept_offer(offer_id: UUID, db: DbSession, user: CandidateUser) -> OfferOut:
    return await offers.accept_offer(db, offer_id=offer_id, candidate=user)


@router.post("/{offer_id}/decline", response_model=OfferOut)
async def decline_offer(offer_id: UUID, db: DbSession, user: CandidateUser) -> OfferOut:
    return await offers.decline_offer(db, offer_id=offer_id, candidate=user)


@router.post("/{offer_id}/withdraw", response_model=OfferOut)
async def withdraw_offer(offer_id: UUID, db: DbSession, user: EmployerUser) -> OfferOut:
    return await offers.withdraw_offer(db, offer_id=offer_id, employer=user)
