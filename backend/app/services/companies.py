"""Employer company profile (one per employer account).

The frontend has no company screen yet and passes only `companyName` on vacancies and
offers, so the company is created on first use and can be edited via /employer/company.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, integrity_constraint_name
from app.models.company import Company
from app.models.user import User
from app.schemas.engagement import CompanyIn, CompanyOut


async def find_company(db: AsyncSession, owner_id: UUID) -> Company | None:
    result = await db.execute(select(Company).where(Company.owner_user_id == owner_id))
    return result.scalar_one_or_none()


async def ensure_company(db: AsyncSession, owner: User, name: str | None) -> Company:
    """The employer's company, created on first use from the given name (no commit)."""
    company = await find_company(db, owner.id)
    if company is None:
        company = Company(
            owner_user_id=owner.id,
            name=(name or owner.display_name or owner.email).strip(),
            contact_name=owner.display_name or None,
            contact_email=owner.email,
        )
        db.add(company)
        await db.flush()
    return company


async def get_company(db: AsyncSession, owner: User) -> CompanyOut:
    company = await find_company(db, owner.id)
    if company is None:
        raise AppError("COMPANY_NOT_FOUND", "Профиль компании ещё не заполнен", 404)
    return CompanyOut.model_validate(company)


async def upsert_company(db: AsyncSession, owner: User, payload: CompanyIn) -> CompanyOut:
    company = await find_company(db, owner.id)
    if company is None:
        company = Company(owner_user_id=owner.id, **payload.model_dump())
        db.add(company)
    else:
        for key, value in payload.model_dump().items():
            setattr(company, key, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        if integrity_constraint_name(exc) == "uq_companies_owner_user_id":
            raise AppError("COMPANY_ALREADY_EXISTS", "Компания уже создана", 409) from exc
        raise
    await db.refresh(company)
    return CompanyOut.model_validate(company)
