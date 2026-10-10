"""Reverse recruiting: employer offers, the candidate's answer and contact disclosure."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload

from app.core.errors import AppError, integrity_constraint_name
from app.models.candidate import CandidateProfile
from app.models.company import Company
from app.models.engagement import Application
from app.models.enums import (
    NotificationType,
    OfferStatus,
    Readiness,
    UserRole,
    UserStatus,
)
from app.models.offer import Offer
from app.models.user import User
from app.models.vacancy import Vacancy
from app.schemas.candidate import CandidateContacts
from app.schemas.offer import EmployerContact, OfferCreate, OfferOut
from app.services import companies
from app.services.audit import write_audit
from app.services.notifications import notify
from app.services.profiles import VISIBLE_PROFILE_VALUES
from app.services.vacancies import CLOSED_STATUSES

# One active offer per employer, candidate and vacancy (or per pair without a vacancy);
# enforced by the partial unique indexes on `offers`.
ACTIVE_STATUSES = (OfferStatus.new.value, OfferStatus.viewed.value)
_ACTIVE_OFFER_INDEXES = {"uq_offers_active_vacancy", "uq_offers_active_no_vacancy"}
_OPTIONS = (selectinload(Offer.employer),)


def _not_found() -> AppError:
    return AppError("OFFER_NOT_FOUND", "Предложение не найдено", 404)


def _offer_exists() -> AppError:
    return AppError(
        "OFFER_ALREADY_EXISTS", "Этому кандидату уже отправлено активное предложение", 409
    )


def to_out(offer: Offer) -> OfferOut:
    """Requires `offer.employer` to be loaded."""
    return OfferOut(
        id=offer.id,
        vacancy_id=offer.vacancy_id,
        candidate_id=offer.candidate_user_id,
        employer_id=offer.employer_user_id,
        employer_name=offer.employer.display_name,
        employer_contact=EmployerContact(**offer.employer_contact),
        company_name=offer.company_name,
        position_title=offer.position_title,
        salary_from=offer.salary_from,
        salary_to=offer.salary_to,
        currency=offer.currency,
        work_format=offer.work_format,
        message=offer.message,
        status=offer.status,
        created_at=offer.sent_at,
        viewed_at=offer.viewed_at,
        responded_at=offer.responded_at,
    )


async def _load(db: AsyncSession, offer_id: UUID) -> Offer:
    result = await db.execute(
        select(Offer)
        .where(Offer.id == offer_id)
        .options(*_OPTIONS)
        .execution_options(populate_existing=True)
    )
    offer = result.scalar_one_or_none()
    if offer is None:
        raise _not_found()
    return offer


async def _list(db: AsyncSession, *conditions) -> list[OfferOut]:
    rows = await db.execute(
        select(Offer).where(*conditions).options(*_OPTIONS).order_by(Offer.sent_at.desc())
    )
    return [to_out(o) for o in rows.scalars().all()]


async def list_for_candidate(db: AsyncSession, user: User) -> list[OfferOut]:
    return await _list(db, Offer.candidate_user_id == user.id)


async def list_for_employer(db: AsyncSession, user: User) -> list[OfferOut]:
    return await _list(db, Offer.employer_user_id == user.id)


async def list_all(db: AsyncSession) -> list[OfferOut]:
    return await _list(db)


async def _ensure_candidate_available(db: AsyncSession, candidate_id: UUID) -> CandidateProfile:
    candidate = await db.get(User, candidate_id)
    profile = await db.get(CandidateProfile, candidate_id)
    if candidate is None or candidate.role != UserRole.candidate.value or profile is None:
        raise AppError("CANDIDATE_NOT_FOUND", "Кандидат не найден", 404)
    if (
        candidate.status != UserStatus.active.value
        or candidate.email_verified_at is None
        or profile.readiness == Readiness.not_looking.value
        or profile.profile_visibility not in VISIBLE_PROFILE_VALUES
    ):
        raise AppError(
            "CANDIDATE_NOT_AVAILABLE", "Кандидат сейчас не рассматривает предложения", 409
        )
    return profile


async def create_offer(db: AsyncSession, *, employer: User, payload: OfferCreate) -> OfferOut:
    if employer.email_verified_at is None:
        raise AppError(
            "EMAIL_NOT_VERIFIED",
            "Подтвердите email, чтобы отправлять предложения: "
            f"письмо отправлено на {employer.email}",
            403,
        )
    company = await companies.ensure_company(db, employer, payload.company_name)
    await _ensure_candidate_available(db, payload.candidate_id)
    if payload.vacancy_id:
        vacancy = await db.get(Vacancy, payload.vacancy_id)
        if vacancy is None or vacancy.company_id != company.id:
            raise AppError("VACANCY_NOT_FOUND", "Вакансия не найдена", 404)
        if vacancy.status in CLOSED_STATUSES:
            raise AppError("VACANCY_CLOSED", "Вакансия закрыта", 409)

    vacancy_filter = (
        Offer.vacancy_id.is_(None)
        if payload.vacancy_id is None
        else Offer.vacancy_id == payload.vacancy_id
    )
    duplicate = await db.execute(
        select(Offer.id).where(
            Offer.employer_user_id == employer.id,
            Offer.candidate_user_id == payload.candidate_id,
            vacancy_filter,
            Offer.status.in_(ACTIVE_STATUSES),
        )
    )
    if duplicate.first() is not None:
        raise _offer_exists()

    # ТЗ: the offer must carry a way to contact the employer.
    contact = payload.employer_contact or EmployerContact(type="email", value=employer.email)
    offer = Offer(
        employer_user_id=employer.id,
        candidate_user_id=payload.candidate_id,
        company_id=company.id,
        vacancy_id=payload.vacancy_id,
        company_name=payload.company_name or company.name,
        position_title=payload.position_title,
        message=payload.message,
        salary_from=payload.salary_from,
        salary_to=payload.salary_to,
        currency=payload.currency,
        work_format=payload.work_format,
        employer_contact=contact.model_dump(),
        status=OfferStatus.new.value,
    )
    db.add(offer)
    try:
        await db.flush()
        notify(
            db,
            user_id=payload.candidate_id,
            type=NotificationType.offer_new,
            title="Новое предложение",
            body=f"{offer.company_name}: {offer.position_title}",
            href=f"/candidate/offers/{offer.id}",
        )
        await write_audit(
            db,
            action="OFFER_SENT",
            entity_type="offer",
            entity_id=str(offer.id),
            actor_user_id=employer.id,
            metadata={"candidate_id": str(payload.candidate_id)},
        )
        await db.commit()
    except IntegrityError as exc:
        # Lost a race with a concurrent request for the same candidate.
        await db.rollback()
        if integrity_constraint_name(exc) in _ACTIVE_OFFER_INDEXES:
            raise _offer_exists() from exc
        raise
    return to_out(await _load(db, offer.id))


async def get_offer(db: AsyncSession, *, offer_id: UUID, user: User) -> OfferOut:
    """Participants only. The candidate's first opening moves `new` to `viewed`."""
    offer = await _load(db, offer_id)
    is_candidate = offer.candidate_user_id == user.id
    if user.role != UserRole.admin.value and not (
        is_candidate or offer.employer_user_id == user.id
    ):
        raise _not_found()  # 404, not 403: do not confirm someone else's offer exists
    if is_candidate and offer.status == OfferStatus.new.value:
        await db.execute(
            update(Offer)
            .where(Offer.id == offer_id, Offer.status == OfferStatus.new.value)
            .values(status=OfferStatus.viewed.value, viewed_at=datetime.now(UTC))
        )
        await db.commit()
        offer = await _load(db, offer_id)
    return to_out(offer)


async def _respond(
    db: AsyncSession,
    *,
    offer_id: UUID,
    actor_id: UUID,
    actor_column: InstrumentedAttribute[UUID],
    new_status: OfferStatus,
    audit_action: str,
) -> Offer:
    """Atomically move an active offer to a final status.

    The status check lives in the UPDATE itself, so a double click or two concurrent
    requests change the offer at most once; the loser gets INVALID_OFFER_STATE.
    """
    result = await db.execute(
        update(Offer)
        .where(Offer.id == offer_id, actor_column == actor_id, Offer.status.in_(ACTIVE_STATUSES))
        .values(status=new_status.value, responded_at=datetime.now(UTC))
        .returning(Offer.id)
    )
    if result.first() is None:
        offer = await db.get(Offer, offer_id)
        if offer is None or getattr(offer, actor_column.key) != actor_id:
            raise _not_found()
        raise AppError(
            "INVALID_OFFER_STATE",
            "Ответ на это предложение уже дан",
            409,
            {"status": offer.status},
        )
    await write_audit(
        db,
        action=audit_action,
        entity_type="offer",
        entity_id=str(offer_id),
        actor_user_id=actor_id,
    )
    return await _load(db, offer_id)


async def _answer(
    db: AsyncSession, offer_id: UUID, candidate: User, status: OfferStatus
) -> OfferOut:
    accepted = status == OfferStatus.accepted
    offer = await _respond(
        db,
        offer_id=offer_id,
        actor_id=candidate.id,
        actor_column=Offer.candidate_user_id,
        new_status=status,
        audit_action="OFFER_ACCEPTED" if accepted else "OFFER_DECLINED",
    )
    notify(
        db,
        user_id=offer.employer_user_id,
        type=NotificationType.offer_accepted if accepted else NotificationType.offer_declined,
        title="Оффер принят" if accepted else "Оффер отклонён",
        body=f"{offer.position_title} · {candidate.display_name}",
        href=(f"/employer/candidates/{candidate.id}" if accepted else "/employer/offers"),
    )
    await db.commit()
    return to_out(offer)


async def accept_offer(db: AsyncSession, *, offer_id: UUID, candidate: User) -> OfferOut:
    return await _answer(db, offer_id, candidate, OfferStatus.accepted)


async def decline_offer(db: AsyncSession, *, offer_id: UUID, candidate: User) -> OfferOut:
    return await _answer(db, offer_id, candidate, OfferStatus.declined)


async def withdraw_offer(db: AsyncSession, *, offer_id: UUID, employer: User) -> OfferOut:
    offer = await _respond(
        db,
        offer_id=offer_id,
        actor_id=employer.id,
        actor_column=Offer.employer_user_id,
        new_status=OfferStatus.withdrawn,
        audit_action="OFFER_WITHDRAWN",
    )
    await db.commit()
    return to_out(offer)


async def _contacts_unlocked(db: AsyncSession, employer_id: UUID, candidate_id: UUID) -> bool:
    """Accepted offer from this employer, or the candidate's own application (ТЗ)."""
    accepted = await db.execute(
        select(Offer.id).where(
            Offer.employer_user_id == employer_id,
            Offer.candidate_user_id == candidate_id,
            Offer.status == OfferStatus.accepted.value,
        )
    )
    if accepted.first() is not None:
        return True
    applied = await db.execute(
        select(Application.id)
        .join(Vacancy, Vacancy.id == Application.vacancy_id)
        .join(Company, Company.id == Vacancy.company_id)
        .where(Application.candidate_user_id == candidate_id, Company.owner_user_id == employer_id)
    )
    return applied.first() is not None


async def candidate_contacts(
    db: AsyncSession, *, candidate_id: UUID, employer: User
) -> CandidateContacts:
    """The only way an employer gets candidate contacts (Backend.md, "Раскрытие контактов")."""
    if not await _contacts_unlocked(db, employer.id, candidate_id):
        raise AppError("CONTACTS_LOCKED", "Контакты доступны после принятия предложения", 403)
    candidate = await db.get(User, candidate_id)
    if candidate is None or candidate.status != UserStatus.active.value:
        raise AppError("CANDIDATE_NOT_AVAILABLE", "Кандидат больше недоступен", 410)
    profile = await db.get(CandidateProfile, candidate_id)
    await write_audit(
        db,
        action="CONTACTS_REVEALED",
        entity_type="candidate",
        entity_id=str(candidate_id),
        actor_user_id=employer.id,
    )
    await db.commit()
    return CandidateContacts(
        email=candidate.email,
        phone=profile.phone if profile else None,
        telegram=profile.telegram if profile else None,
    )
