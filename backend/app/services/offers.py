from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.candidate import CandidateProfile
from app.models.company import Company
from app.models.enums import OfferStatus, UserStatus, VacancyStatus
from app.models.offer import Offer
from app.models.user import User
from app.models.vacancy import Vacancy
from app.schemas.offer import (
    CandidateContactOut,
    CompanyBrief,
    EmployerContact,
    OfferCreate,
    OfferOut,
)
from app.services.audit import write_audit

ACTIVE_STATUSES = {OfferStatus.sent.value, OfferStatus.viewed.value}


async def _company_for_employer(db: AsyncSession, employer_id: UUID) -> Company:
    result = await db.execute(select(Company).where(Company.owner_user_id == employer_id))
    company = result.scalars().first()
    if company is None:
        raise AppError("COMPANY_REQUIRED", "Create a company first", 409)
    return company


def to_out(offer: Offer, company: Company) -> OfferOut:
    return OfferOut(
        id=offer.id,
        candidate_id=offer.candidate_user_id,
        employer_user_id=offer.employer_user_id,
        company=CompanyBrief(id=company.id, name=company.name),
        vacancy_id=offer.vacancy_id,
        title=offer.title,
        description=offer.description,
        salary_from=offer.salary_from,
        salary_to=offer.salary_to,
        currency=offer.currency,
        work_format=offer.work_format,
        employer_contact=EmployerContact(**offer.employer_contact),
        status=offer.status,
        created_at=offer.sent_at,
        viewed_at=offer.viewed_at,
        responded_at=offer.responded_at,
    )


async def create_offer(
    db: AsyncSession, *, employer_id: UUID, payload: OfferCreate
) -> OfferOut:
    company = await _company_for_employer(db, employer_id)
    candidate = await db.get(User, payload.candidate_id)
    if candidate is None or candidate.role != "candidate":
        raise AppError("CANDIDATE_NOT_FOUND", "Candidate not found", 404)
    if candidate.status != UserStatus.active.value:
        raise AppError("CANDIDATE_NOT_AVAILABLE", "Candidate is not available", 409)
    profile = await db.get(CandidateProfile, payload.candidate_id)
    if profile is None or not profile.open_to_offers:
        raise AppError("CANDIDATE_NOT_AVAILABLE", "Candidate is not accepting offers", 409)

    if payload.vacancy_id:
        vacancy = await db.get(Vacancy, payload.vacancy_id)
        if vacancy is None or vacancy.company_id != company.id:
            raise AppError("VACANCY_NOT_FOUND", "Vacancy not found for company", 404)
        if vacancy.status == VacancyStatus.closed.value:
            raise AppError("VACANCY_CLOSED", "Vacancy is closed", 409)
        dup = await db.execute(
            select(Offer).where(
                Offer.candidate_user_id == payload.candidate_id,
                Offer.vacancy_id == payload.vacancy_id,
                Offer.status.in_(list(ACTIVE_STATUSES)),
            )
        )
        if dup.scalar_one_or_none():
            raise AppError("OFFER_ALREADY_EXISTS", "Active offer already exists", 409)

    offer = Offer(
        employer_user_id=employer_id,
        candidate_user_id=payload.candidate_id,
        company_id=company.id,
        vacancy_id=payload.vacancy_id,
        title=payload.title,
        description=payload.description,
        salary_from=payload.salary_from,
        salary_to=payload.salary_to,
        currency=payload.currency,
        work_format=payload.work_format,
        employer_contact=payload.employer_contact.model_dump(),
        status=OfferStatus.sent.value,
    )
    db.add(offer)
    await db.flush()
    await write_audit(
        db,
        action="OFFER_SENT",
        entity_type="offer",
        entity_id=str(offer.id),
        actor_user_id=employer_id,
        metadata={"candidate_id": str(payload.candidate_id)},
    )
    await db.commit()
    await db.refresh(offer)
    return to_out(offer, company)


async def list_offers(db: AsyncSession, *, user: User) -> list[OfferOut]:
    if user.role == "employer":
        stmt = select(Offer).where(Offer.employer_user_id == user.id)
    elif user.role == "candidate":
        stmt = select(Offer).where(Offer.candidate_user_id == user.id)
    else:
        stmt = select(Offer)
    offers = (await db.execute(stmt.order_by(Offer.sent_at.desc()))).scalars().all()
    out: list[OfferOut] = []
    for o in offers:
        company = await db.get(Company, o.company_id)
        if company:
            out.append(to_out(o, company))
    return out


async def get_offer_for_participant(
    db: AsyncSession, *, offer_id: UUID, user: User
) -> tuple[Offer, Company]:
    offer = await db.get(Offer, offer_id)
    if offer is None:
        raise AppError("OFFER_NOT_FOUND", "Offer not found", 404)
    if user.role == "admin":
        pass
    elif user.role == "employer" and offer.employer_user_id != user.id:
        raise AppError("FORBIDDEN_ROLE", "Not your offer", 403)
    elif user.role == "candidate" and offer.candidate_user_id != user.id:
        raise AppError("FORBIDDEN_ROLE", "Not your offer", 403)
    company = await db.get(Company, offer.company_id)
    assert company is not None
    return offer, company


async def view_offer(db: AsyncSession, *, offer_id: UUID, candidate_id: UUID) -> OfferOut:
    offer = await db.get(Offer, offer_id)
    if offer is None or offer.candidate_user_id != candidate_id:
        raise AppError("OFFER_NOT_FOUND", "Offer not found", 404)
    if offer.status == OfferStatus.sent.value:
        offer.status = OfferStatus.viewed.value
        offer.viewed_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(offer)
    company = await db.get(Company, offer.company_id)
    assert company
    return to_out(offer, company)


async def accept_offer(db: AsyncSession, *, offer_id: UUID, candidate_id: UUID) -> OfferOut:
    result = await db.execute(
        update(Offer)
        .where(
            Offer.id == offer_id,
            Offer.candidate_user_id == candidate_id,
            Offer.status.in_([OfferStatus.sent.value, OfferStatus.viewed.value]),
        )
        .values(status=OfferStatus.accepted.value, responded_at=datetime.now(UTC))
        .returning(Offer.id)
    )
    row = result.first()
    if row is None:
        raise AppError("INVALID_OFFER_STATE", "Offer cannot be accepted in current state", 409)
    await write_audit(
        db,
        action="OFFER_ACCEPTED",
        entity_type="offer",
        entity_id=str(offer_id),
        actor_user_id=candidate_id,
    )
    await db.commit()
    offer = await db.get(Offer, offer_id)
    company = await db.get(Company, offer.company_id)
    return to_out(offer, company)


async def reject_offer(db: AsyncSession, *, offer_id: UUID, candidate_id: UUID) -> OfferOut:
    result = await db.execute(
        update(Offer)
        .where(
            Offer.id == offer_id,
            Offer.candidate_user_id == candidate_id,
            Offer.status.in_([OfferStatus.sent.value, OfferStatus.viewed.value]),
        )
        .values(status=OfferStatus.rejected.value, responded_at=datetime.now(UTC))
        .returning(Offer.id)
    )
    if result.first() is None:
        raise AppError("INVALID_OFFER_STATE", "Offer cannot be rejected in current state", 409)
    await write_audit(
        db,
        action="OFFER_REJECTED",
        entity_type="offer",
        entity_id=str(offer_id),
        actor_user_id=candidate_id,
    )
    await db.commit()
    offer = await db.get(Offer, offer_id)
    company = await db.get(Company, offer.company_id)
    return to_out(offer, company)


async def withdraw_offer(db: AsyncSession, *, offer_id: UUID, employer_id: UUID) -> OfferOut:
    result = await db.execute(
        update(Offer)
        .where(
            Offer.id == offer_id,
            Offer.employer_user_id == employer_id,
            Offer.status.in_([OfferStatus.sent.value, OfferStatus.viewed.value]),
        )
        .values(status=OfferStatus.withdrawn.value, responded_at=datetime.now(UTC))
        .returning(Offer.id)
    )
    if result.first() is None:
        raise AppError("INVALID_OFFER_STATE", "Offer cannot be withdrawn", 409)
    await db.commit()
    offer = await db.get(Offer, offer_id)
    company = await db.get(Company, offer.company_id)
    return to_out(offer, company)


async def candidate_contact(
    db: AsyncSession, *, offer_id: UUID, employer_id: UUID
) -> CandidateContactOut:
    offer = await db.get(Offer, offer_id)
    if offer is None or offer.employer_user_id != employer_id:
        raise AppError("OFFER_NOT_FOUND", "Offer not found", 404)
    if offer.status != OfferStatus.accepted.value:
        raise AppError(
            "CONTACTS_LOCKED",
            "Контакты кандидата будут доступны после принятия приглашения",
            403,
        )
    user = await db.get(User, offer.candidate_user_id)
    profile = await db.get(CandidateProfile, offer.candidate_user_id)
    await write_audit(
        db,
        action="CONTACTS_REVEALED",
        entity_type="offer",
        entity_id=str(offer.id),
        actor_user_id=employer_id,
        metadata={"candidate_id": str(offer.candidate_user_id)},
    )
    await db.commit()
    return CandidateContactOut(
        candidate_id=offer.candidate_user_id,
        contact={
            "email": user.email if user else None,
            "phone": profile.phone if profile else None,
            "telegram": profile.telegram if profile else None,
        },
    )
