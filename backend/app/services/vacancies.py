from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.candidate import CandidateProfile
from app.models.company import Company
from app.models.engagement import Application, SavedVacancy
from app.models.enums import NotificationType, UserRole, VacancyStatus
from app.models.taxonomy import Skill
from app.models.user import User
from app.models.vacancy import Vacancy, VacancySkill
from app.schemas.candidate import CandidateMatch
from app.schemas.vacancy import (
    ApplyResponse,
    SavedResponse,
    VacancyCreate,
    VacancyOut,
    VacancyUpdate,
    VacancyWithMatch,
)
from app.services import companies, matching, taxonomy
from app.services.audit import write_audit
from app.services.notifications import notify

REQUIRED_SKILL_WEIGHT = 2
OPTIONAL_SKILL_WEIGHT = 1
CLOSED_STATUSES = {VacancyStatus.closed.value, VacancyStatus.archived.value}


def _not_found() -> AppError:
    return AppError("VACANCY_NOT_FOUND", "Вакансия не найдена", 404)


def to_out(vacancy: Vacancy) -> VacancyOut:
    """Requires matching.VACANCY_OPTIONS to be loaded."""
    return VacancyOut(
        id=vacancy.id,
        employer_id=vacancy.company.owner_user_id,
        company_name=vacancy.company_name or vacancy.company.name,
        title=vacancy.title,
        description=vacancy.description,
        specialization=vacancy.specialization.name,
        required_grade=vacancy.grade.code,
        required_skills=[s.skill.name for s in vacancy.skills if s.required],
        nice_to_have_skills=[s.skill.name for s in vacancy.skills if not s.required],
        salary_from=vacancy.salary_from,
        salary_to=vacancy.salary_to,
        currency=vacancy.currency,
        city=vacancy.city,
        work_format=vacancy.work_format,
        extra_info=vacancy.extra_info,
        status=vacancy.status,
        created_at=vacancy.created_at,
        updated_at=vacancy.updated_at,
    )


async def load_vacancy(db: AsyncSession, vacancy_id: UUID) -> Vacancy:
    result = await db.execute(
        select(Vacancy)
        .where(Vacancy.id == vacancy_id)
        .options(*matching.VACANCY_OPTIONS)
        .execution_options(populate_existing=True)
    )
    vacancy = result.scalar_one_or_none()
    if vacancy is None:
        raise _not_found()
    return vacancy


def can_manage(vacancy: Vacancy, user: User) -> bool:
    return user.role == UserRole.admin.value or vacancy.company.owner_user_id == user.id


async def get_editable(db: AsyncSession, vacancy_id: UUID, user: User) -> Vacancy:
    vacancy = await load_vacancy(db, vacancy_id)
    if not can_manage(vacancy, user):
        raise _not_found()
    return vacancy


async def get_vacancy(db: AsyncSession, vacancy_id: UUID, user: User) -> VacancyOut:
    vacancy = await load_vacancy(db, vacancy_id)
    # Active vacancies are visible to every signed-in user, the rest only to the owner.
    if vacancy.status != VacancyStatus.active.value and not can_manage(vacancy, user):
        raise _not_found()
    return to_out(vacancy)


async def list_owned(db: AsyncSession, user: User) -> list[VacancyOut]:
    rows = await db.execute(
        select(Vacancy)
        .join(Company, Company.id == Vacancy.company_id)
        .where(Company.owner_user_id == user.id)
        .options(*matching.VACANCY_OPTIONS)
        .order_by(Vacancy.created_at.desc())
    )
    return [to_out(v) for v in rows.scalars().all()]


async def list_all(db: AsyncSession) -> list[VacancyOut]:
    rows = await db.execute(
        select(Vacancy).options(*matching.VACANCY_OPTIONS).order_by(Vacancy.created_at.desc())
    )
    return [to_out(v) for v in rows.scalars().all()]


def _skill_rows(required: list[Skill], optional: list[Skill]) -> list[VacancySkill]:
    required_ids = {s.id for s in required}
    return [
        *(VacancySkill(skill=s, required=True, weight=REQUIRED_SKILL_WEIGHT) for s in required),
        *(
            VacancySkill(skill=s, required=False, weight=OPTIONAL_SKILL_WEIGHT)
            for s in optional
            if s.id not in required_ids  # listed in both: it is required
        ),
    ]


async def create_vacancy(db: AsyncSession, *, user: User, payload: VacancyCreate) -> VacancyOut:
    company = await companies.ensure_company(db, user, payload.company_name)
    spec = await taxonomy.specialization_by_name(db, payload.specialization)
    grade = await taxonomy.grade_by_code(db, payload.required_grade)
    required = await taxonomy.resolve_skills(db, payload.required_skills)
    optional = await taxonomy.resolve_skills(db, payload.nice_to_have_skills)
    vacancy = Vacancy(
        company_id=company.id,
        company_name=payload.company_name or company.name,
        title=payload.title,
        description=payload.description,
        specialization_id=spec.id,
        grade_id=grade.id,
        salary_from=payload.salary_from,
        salary_to=payload.salary_to,
        currency=payload.currency,
        city=payload.city,
        work_format=payload.work_format,
        extra_info=payload.extra_info,
        status=payload.status,
        skills=_skill_rows(required, optional),
    )
    db.add(vacancy)
    await db.flush()
    await write_audit(
        db,
        action="VACANCY_CREATED",
        entity_type="vacancy",
        entity_id=str(vacancy.id),
        actor_user_id=user.id,
    )
    await db.commit()
    return to_out(await load_vacancy(db, vacancy.id))


async def update_vacancy(
    db: AsyncSession, *, vacancy_id: UUID, user: User, payload: VacancyUpdate
) -> VacancyOut:
    vacancy = await get_editable(db, vacancy_id, user)
    data = payload.model_dump(
        exclude_unset=True,
        exclude={"specialization", "required_grade", "required_skills", "nice_to_have_skills"},
    )
    salary_from = data.get("salary_from", vacancy.salary_from)
    salary_to = data.get("salary_to", vacancy.salary_to)
    if salary_to < salary_from:
        raise AppError("INVALID_SALARY_RANGE", "Верхняя граница зарплаты меньше нижней", 422)

    if payload.specialization is not None:
        vacancy.specialization_id = (
            await taxonomy.specialization_by_name(db, payload.specialization)
        ).id
    if payload.required_grade is not None:
        vacancy.grade_id = (await taxonomy.grade_by_code(db, payload.required_grade)).id
    if payload.required_skills is not None or payload.nice_to_have_skills is not None:
        current_required = [s.skill.name for s in vacancy.skills if s.required]
        current_optional = [s.skill.name for s in vacancy.skills if not s.required]
        required = await taxonomy.resolve_skills(
            db, payload.required_skills if payload.required_skills is not None else current_required
        )
        optional = await taxonomy.resolve_skills(
            db,
            payload.nice_to_have_skills
            if payload.nice_to_have_skills is not None
            else current_optional,
        )
        vacancy.skills.clear()
        # Delete old rows first: re-adding a kept skill must not hit uq_vacancy_skill.
        await db.flush()
        vacancy.skills.extend(_skill_rows(required, optional))
    for key, value in data.items():
        setattr(vacancy, key, value)
    await db.commit()
    return to_out(await load_vacancy(db, vacancy.id))


async def _candidate_profile(db: AsyncSession, user: User) -> CandidateProfile:
    result = await db.execute(
        select(CandidateProfile)
        .where(CandidateProfile.user_id == user.id)
        .options(*matching.MATCH_PROFILE_OPTIONS)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise AppError("PROFILE_NOT_FOUND", "Профиль не найден", 404)
    return profile


async def _vacancy_ids(
    db: AsyncSession, model: type[Application | SavedVacancy], user_id: UUID
) -> set[UUID]:
    rows = await db.execute(select(model.vacancy_id).where(model.candidate_user_id == user_id))
    return set(rows.scalars().all())


async def catalog(
    db: AsyncSession,
    *,
    user: User,
    specialization: str | None,
    match_to_me: bool,
    saved_only: bool,
) -> list[VacancyWithMatch]:
    """Active vacancies; for candidates with saved/applied flags and an optional match."""
    stmt = (
        select(Vacancy)
        .where(Vacancy.status == VacancyStatus.active.value)
        .options(*matching.VACANCY_OPTIONS)
        .order_by(Vacancy.created_at.desc())
    )
    if specialization:
        spec = await taxonomy.specialization_by_name(db, specialization)
        stmt = stmt.where(Vacancy.specialization_id == spec.id)
    vacancies = list((await db.execute(stmt)).scalars().all())

    if user.role != UserRole.candidate.value:
        return [VacancyWithMatch(**to_out(v).model_dump()) for v in vacancies]

    saved = await _vacancy_ids(db, SavedVacancy, user.id)
    applied = await _vacancy_ids(db, Application, user.id)
    if saved_only:
        vacancies = [v for v in vacancies if v.id in saved]
    matches: dict[UUID, CandidateMatch] = {}
    if match_to_me:
        profile = await _candidate_profile(db, user)
        for vacancy in vacancies:
            found = await matching.match_profiles(vacancy, [profile])
            if user.id in found:
                matches[vacancy.id] = found[user.id]

    items = [
        VacancyWithMatch(
            **to_out(v).model_dump(),
            match=matches.get(v.id),
            saved=v.id in saved,
            applied=v.id in applied,
        )
        for v in vacancies
    ]
    if match_to_me:
        items.sort(key=lambda item: -(item.match.score if item.match else 0))
    return items


async def match_to_me(db: AsyncSession, user: User, vacancy_id: UUID) -> CandidateMatch:
    vacancy = await load_vacancy(db, vacancy_id)
    if vacancy.status != VacancyStatus.active.value:
        raise _not_found()
    profile = await _candidate_profile(db, user)
    match = (await matching.match_profiles(vacancy, [profile])).get(user.id)
    if match is None:  # an external matcher dropped the candidate
        raise AppError(
            "MATCH_UNAVAILABLE", "Не удалось рассчитать совпадение, попробуйте позже", 503
        )
    return match


async def apply(db: AsyncSession, user: User, vacancy_id: UUID) -> ApplyResponse:
    vacancy = await load_vacancy(db, vacancy_id)
    if vacancy.status != VacancyStatus.active.value:
        raise AppError("VACANCY_CLOSED", "Вакансия больше не принимает отклики", 409)
    profile = await _candidate_profile(db, user)
    existing = await db.execute(
        select(Application.id).where(
            Application.candidate_user_id == user.id, Application.vacancy_id == vacancy_id
        )
    )
    if existing.first() is not None:
        return ApplyResponse(message="Вы уже откликнулись на эту вакансию")
    db.add(Application(candidate_user_id=user.id, vacancy_id=vacancy_id))
    notify(
        db,
        user_id=vacancy.company.owner_user_id,
        type=NotificationType.application,
        title="Новый отклик",
        body=f"{profile.full_name or 'Кандидат'} откликнулся на «{vacancy.title}»",
        href=f"/employer/candidates/{user.id}?vacancyId={vacancy.id}",
    )
    await write_audit(
        db,
        action="APPLICATION_SENT",
        entity_type="vacancy",
        entity_id=str(vacancy_id),
        actor_user_id=user.id,
    )
    try:
        await db.commit()
    except IntegrityError:
        # A double click raced with itself; the first one already applied.
        await db.rollback()
    return ApplyResponse(message="Отклик отправлен")


async def saved_list(db: AsyncSession, user: User) -> list[VacancyOut]:
    rows = await db.execute(
        select(Vacancy)
        .join(SavedVacancy, SavedVacancy.vacancy_id == Vacancy.id)
        .where(SavedVacancy.candidate_user_id == user.id)
        .options(*matching.VACANCY_OPTIONS)
        .order_by(SavedVacancy.created_at.desc())
    )
    return [to_out(v) for v in rows.scalars().all()]


async def save(db: AsyncSession, user: User, vacancy_id: UUID) -> SavedResponse:
    await load_vacancy(db, vacancy_id)
    if vacancy_id not in await _vacancy_ids(db, SavedVacancy, user.id):
        db.add(SavedVacancy(candidate_user_id=user.id, vacancy_id=vacancy_id))
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
    return SavedResponse(saved=True)


async def unsave(db: AsyncSession, user: User, vacancy_id: UUID) -> SavedResponse:
    rows = await db.execute(
        select(SavedVacancy).where(
            SavedVacancy.candidate_user_id == user.id, SavedVacancy.vacancy_id == vacancy_id
        )
    )
    for row in rows.scalars().all():
        await db.delete(row)
    await db.commit()
    return SavedResponse(saved=False)
