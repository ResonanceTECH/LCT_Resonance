from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DbSession, require_roles
from app.core.errors import AppError
from app.models.company import Company
from app.models.enums import UserRole, VacancyStatus
from app.models.user import User
from app.models.vacancy import Vacancy, VacancySkill
from app.schemas.vacancy import VacancyCreate, VacancyOut, VacancySkillIn, VacancyUpdate
from app.services.audit import write_audit

router = APIRouter(tags=["vacancies"])


def _to_out(v: Vacancy) -> VacancyOut:
    return VacancyOut(
        id=v.id,
        company_id=v.company_id,
        title=v.title,
        description=v.description,
        specialization_id=v.specialization_id,
        grade_id=v.grade_id,
        salary_from=v.salary_from,
        salary_to=v.salary_to,
        currency=v.currency,
        work_format=v.work_format,
        visibility=v.visibility,
        status=v.status,
        skills=[
            VacancySkillIn(skill_id=s.skill_id, required=s.required, weight=s.weight)
            for s in v.skills
        ],
    )


async def _owner_company(db, user_id: UUID) -> Company:
    company = (
        await db.execute(select(Company).where(Company.owner_user_id == user_id))
    ).scalars().first()
    if company is None:
        raise AppError("COMPANY_REQUIRED", "Create a company first", 409)
    return company


@router.post("/vacancies", response_model=VacancyOut, status_code=201)
async def create_vacancy(
    payload: VacancyCreate,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer, UserRole.admin)),
) -> VacancyOut:
    company = await _owner_company(db, user.id)
    data = payload.model_dump(exclude={"skills"})
    vacancy = Vacancy(company_id=company.id, **data)
    db.add(vacancy)
    await db.flush()
    for s in payload.skills:
        db.add(
            VacancySkill(
                vacancy_id=vacancy.id,
                skill_id=s.skill_id,
                required=s.required,
                weight=s.weight if s.weight is not None else (2 if s.required else 1),
            )
        )
    await write_audit(
        db,
        action="VACANCY_CREATED",
        entity_type="vacancy",
        entity_id=str(vacancy.id),
        actor_user_id=user.id,
    )
    await db.commit()
    result = await db.execute(
        select(Vacancy).where(Vacancy.id == vacancy.id).options(selectinload(Vacancy.skills))
    )
    return _to_out(result.scalar_one())


@router.get("/vacancies", response_model=list[VacancyOut])
async def list_vacancies(db: DbSession) -> list[VacancyOut]:
    rows = (
        await db.execute(
            select(Vacancy)
            .where(Vacancy.status == VacancyStatus.published.value)
            .options(selectinload(Vacancy.skills))
        )
    ).scalars().all()
    return [_to_out(v) for v in rows]


@router.get("/companies/me/vacancies", response_model=list[VacancyOut])
async def my_vacancies(
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer, UserRole.admin)),
) -> list[VacancyOut]:
    company = await _owner_company(db, user.id)
    rows = (
        await db.execute(
            select(Vacancy)
            .where(Vacancy.company_id == company.id)
            .options(selectinload(Vacancy.skills))
        )
    ).scalars().all()
    return [_to_out(v) for v in rows]


@router.get("/vacancies/{vacancy_id}", response_model=VacancyOut)
async def get_vacancy(vacancy_id: UUID, db: DbSession) -> VacancyOut:
    result = await db.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id).options(selectinload(Vacancy.skills))
    )
    vacancy = result.scalar_one_or_none()
    if vacancy is None:
        raise AppError("VACANCY_NOT_FOUND", "Vacancy not found", 404)
    return _to_out(vacancy)


@router.patch("/vacancies/{vacancy_id}", response_model=VacancyOut)
async def patch_vacancy(
    vacancy_id: UUID,
    payload: VacancyUpdate,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer, UserRole.admin)),
) -> VacancyOut:
    company = await _owner_company(db, user.id)
    result = await db.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id).options(selectinload(Vacancy.skills))
    )
    vacancy = result.scalar_one_or_none()
    if vacancy is None or vacancy.company_id != company.id:
        raise AppError("VACANCY_NOT_FOUND", "Vacancy not found", 404)
    data = payload.model_dump(exclude_unset=True, exclude={"skills"})
    for k, v in data.items():
        setattr(vacancy, k, v)
    if payload.skills is not None:
        vacancy.skills.clear()
        await db.flush()
        for s in payload.skills:
            db.add(
                VacancySkill(
                    vacancy_id=vacancy.id,
                    skill_id=s.skill_id,
                    required=s.required,
                    weight=s.weight if s.weight is not None else (2 if s.required else 1),
                )
            )
    await db.commit()
    result = await db.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id).options(selectinload(Vacancy.skills))
    )
    return _to_out(result.scalar_one())


@router.delete("/vacancies/{vacancy_id}", status_code=204)
async def delete_vacancy(
    vacancy_id: UUID,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer, UserRole.admin)),
) -> None:
    company = await _owner_company(db, user.id)
    vacancy = await db.get(Vacancy, vacancy_id)
    if vacancy is None or vacancy.company_id != company.id:
        raise AppError("VACANCY_NOT_FOUND", "Vacancy not found", 404)
    if vacancy.status != VacancyStatus.draft.value:
        raise AppError("VACANCY_NOT_DRAFT", "Only draft vacancies can be deleted", 409)
    await db.delete(vacancy)
    await db.commit()


@router.post("/vacancies/{vacancy_id}/publish", response_model=VacancyOut)
async def publish_vacancy(
    vacancy_id: UUID,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer, UserRole.admin)),
) -> VacancyOut:
    company = await _owner_company(db, user.id)
    result = await db.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id).options(selectinload(Vacancy.skills))
    )
    vacancy = result.scalar_one_or_none()
    if vacancy is None or vacancy.company_id != company.id:
        raise AppError("VACANCY_NOT_FOUND", "Vacancy not found", 404)
    vacancy.status = VacancyStatus.published.value
    await db.commit()
    await db.refresh(vacancy)
    return _to_out(vacancy)


@router.post("/vacancies/{vacancy_id}/close", response_model=VacancyOut)
async def close_vacancy(
    vacancy_id: UUID,
    db: DbSession,
    user: User = Depends(require_roles(UserRole.employer, UserRole.admin)),
) -> VacancyOut:
    company = await _owner_company(db, user.id)
    result = await db.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id).options(selectinload(Vacancy.skills))
    )
    vacancy = result.scalar_one_or_none()
    if vacancy is None or vacancy.company_id != company.id:
        raise AppError("VACANCY_NOT_FOUND", "Vacancy not found", 404)
    vacancy.status = VacancyStatus.closed.value
    await db.commit()
    await db.refresh(vacancy)
    return _to_out(vacancy)
