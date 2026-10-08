from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.deps import DbSession, require_roles
from app.core.errors import AppError
from app.models.company import Company
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyOut, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyOut, status_code=201)
async def create_company(
    payload: CompanyCreate,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer, UserRole.admin)),
) -> CompanyOut:
    company = Company(owner_user_id=user.id, **payload.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return CompanyOut.model_validate(company)


@router.get("/me", response_model=list[CompanyOut])
async def my_companies(
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer, UserRole.admin)),
) -> list[CompanyOut]:
    rows = (
        await db.execute(select(Company).where(Company.owner_user_id == user.id))
    ).scalars().all()
    return [CompanyOut.model_validate(r) for r in rows]


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(company_id: UUID, db: DbSession) -> CompanyOut:
    company = await db.get(Company, company_id)
    if company is None:
        raise AppError("COMPANY_NOT_FOUND", "Company not found", 404)
    return CompanyOut.model_validate(company)


@router.patch("/{company_id}", response_model=CompanyOut)
async def patch_company(
    company_id: UUID,
    payload: CompanyUpdate,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer, UserRole.admin)),
) -> CompanyOut:
    company = await db.get(Company, company_id)
    if company is None or company.owner_user_id != user.id:
        raise AppError("COMPANY_NOT_FOUND", "Company not found", 404)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(company, k, v)
    await db.commit()
    await db.refresh(company)
    return CompanyOut.model_validate(company)


@router.delete("/{company_id}", status_code=204)
async def delete_company(
    company_id: UUID,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer, UserRole.admin)),
) -> None:
    company = await db.get(Company, company_id)
    if company is None or company.owner_user_id != user.id:
        raise AppError("COMPANY_NOT_FOUND", "Company not found", 404)
    await db.delete(company)
    await db.commit()
