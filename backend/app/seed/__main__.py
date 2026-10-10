"""Demo data: `python -m app.seed`. Idempotent: a second run prints SEED_SKIP."""

from __future__ import annotations

import asyncio
import random
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.integrations.fsp.mock import MockFSPAdapter
from app.models.candidate import CandidateProfile, CandidateSkill, Consent
from app.models.company import Company
from app.models.engagement import (
    Application,
    Notification,
    ProfileView,
    SavedVacancy,
    ShortlistItem,
)
from app.models.enums import (
    ConsentType,
    FspSyncStatus,
    GradeVerificationStatus,
    NotificationType,
    OfferStatus,
    TestAttemptStatus,
    UserRole,
)
from app.models.fsp import FspAchievement, FspLink
from app.models.offer import Offer
from app.models.taxonomy import Grade, Skill, Specialization
from app.models.testing import TestAttempt, TestQuestion
from app.models.user import User
from app.models.vacancy import Vacancy, VacancySkill
from app.seed import data
from app.seed.questions import QUESTION_BANK

# Fixed seed: every run produces the same demo, so screenshots and Precision@k stay stable.
RNG_SEED = 2026


class _Seeder:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.rng = random.Random(RNG_SEED)
        self.now = datetime.now(UTC)
        # One Argon2 hash for every demo account: hashing is deliberately slow.
        self.password_hash = hash_password(data.DEMO_PASSWORD)
        self.specs: dict[str, Specialization] = {}
        self.grades: dict[str, Grade] = {}
        self.skills: dict[str, Skill] = {}
        self.users: dict[str, User] = {}
        self.companies: dict[str, Company] = {}
        self.vacancy_index: dict[tuple[str, str], Vacancy] = {}
        self.candidates_seeded: list[tuple[User, data.SeedCandidate]] = []

    def _user(self, email: str, role: UserRole, display_name: str) -> User:
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=self.password_hash,
            display_name=display_name,
            role=role.value,
            email_verified_at=self.now,
        )
        self.db.add(user)
        self.users[email] = user
        return user

    def _demo_phone(self) -> str:
        r = self.rng.randint
        return f"+7 900 {r(100, 999)}-{r(10, 99)}-{r(10, 99)}"

    def taxonomy(self) -> None:
        self.specs = {
            slug: Specialization(id=uuid.uuid4(), slug=slug, name=name)
            for slug, name in data.SPECIALIZATIONS
        }
        self.grades = {
            code: Grade(id=uuid.uuid4(), code=code, rank=rank, name=name)
            for code, rank, name in data.GRADES
        }
        self.skills = {
            slug: Skill(id=uuid.uuid4(), slug=slug, name=name) for slug, name in data.SKILLS
        }
        self.db.add_all([*self.specs.values(), *self.grades.values(), *self.skills.values()])

    def questions(self) -> None:
        for (spec, grade), questions in QUESTION_BANK.items():
            self.db.add_all(
                TestQuestion(
                    specialization_id=self.specs[spec].id,
                    grade_id=self.grades[grade].id,
                    topic=q.topic,
                    prompt=q.prompt,
                    options=q.options_json(),
                    correct_answer=q.correct,
                )
                for q in questions
            )

    def employers(self) -> None:
        self._user(data.ADMIN_EMAIL, UserRole.admin, "Админ Resonance")
        for employer in data.EMPLOYERS:
            user = self._user(employer.email, UserRole.employer, employer.display_name)
            company = Company(
                id=uuid.uuid4(),
                owner=user,
                name=employer.company_name,
                description=employer.description,
                industry=employer.industry,
                contact_name=employer.display_name,
                contact_email=employer.email,
            )
            self.db.add(company)
            self.companies[employer.email] = company

    def _filler_candidates(self) -> list[data.SeedCandidate]:
        """Volume for search and pagination, seeded without FSP data (ТЗ edge case).

        candidate1@demo.ru is in the mock registry: its first sync links it automatically.
        """
        result = []
        for i, name in enumerate(data.FILLER_NAMES, start=1):
            spec = "backend" if i % 2 else "frontend"
            tested = i % 4 != 0  # every 4th candidate has not taken a test yet
            salary_from = self.rng.randrange(150000, 300000, 10000)
            result.append(
                data.SeedCandidate(
                    email=f"candidate{i}@demo.ru",
                    full_name=name,
                    specialization=spec,
                    grade=self.rng.choice(["middle", "middle", "junior"]) if tested else None,
                    test_score=self.rng.randint(70, 95) if tested else None,
                    skills=tuple(self.rng.sample(data.SKILL_POOLS[spec], 3)),
                    salary_from=salary_from,
                    salary_to=salary_from + 60000,
                    work_format=self.rng.choice(["remote", "hybrid", "office"]),
                    city=self.rng.choice(data.CITIES),
                    desired_position=f"{spec.capitalize()} Developer",
                    experience_years=self.rng.randint(1, 6),
                    readiness="not_looking" if i == len(data.FILLER_NAMES) else "open_to_offers",
                )
            )
        return result

    def candidates(self) -> None:
        for seed in [*data.NAMED_CANDIDATES, *self._filler_candidates()]:
            user = self._user(seed.email, UserRole.candidate, seed.full_name)
            spec = self.specs[seed.specialization]
            verified_grade = self.grades[seed.grade] if seed.grade else None
            profile = CandidateProfile(
                user=user,
                full_name=seed.full_name,
                about=seed.about or None,
                phone=self._demo_phone(),
                telegram=f"@{seed.email.split('@')[0].replace('.', '_')}_demo",
                city=seed.city,
                experience_years=seed.experience_years,
                desired_position=seed.desired_position or None,
                declared_specialization_id=spec.id,
                declared_grade_id=(verified_grade or self.grades["middle"]).id,
                verified_specialization_id=spec.id if verified_grade else None,
                verified_grade_id=verified_grade.id if verified_grade else None,
                grade_verification_status=(
                    GradeVerificationStatus.verified.value
                    if verified_grade
                    else GradeVerificationStatus.not_tested.value
                ),
                last_grade_change_at=self.now if verified_grade else None,
                last_test_score=seed.test_score,
                salary_from=seed.salary_from,
                salary_to=seed.salary_to,
                work_format=seed.work_format,
                readiness=seed.readiness,
                skills=[CandidateSkill(skill=self.skills[s], level=4) for s in seed.skills],
            )
            self.db.add(profile)
            self.candidates_seeded.append((user, seed))

    async def after_profiles(self) -> None:
        """Rows that reference profiles without an ORM relationship: the unit of work
        cannot order these inserts by itself, so they go after the profiles are flushed."""
        fsp = MockFSPAdapter()
        version = get_settings().consent_version
        for user, seed in self.candidates_seeded:
            self.db.add_all(
                Consent(user_id=user.id, type=t.value, version=version, accepted_at=self.now)
                for t in ConsentType
            )
            if seed.grade and seed.test_score is not None:
                # The passed test behind the confirmed grade (shown as `testResult`).
                finished = self.now - timedelta(days=self.rng.randint(3, 30))
                self.db.add(
                    TestAttempt(
                        candidate_user_id=user.id,
                        specialization_id=self.specs[seed.specialization].id,
                        grade_id=self.grades[seed.grade].id,
                        status=TestAttemptStatus.completed.value,
                        score=seed.test_score,
                        passed=True,
                        current_index=10,
                        expires_at=finished,
                        submitted_at=finished,
                    )
                )
            if seed.fsp_member_id:
                await self._fsp(user, seed.fsp_member_id, fsp)

    async def _fsp(self, user: User, member_id: str, fsp: MockFSPAdapter) -> None:
        """Same data a real sync would fetch from the mock registry."""
        member = await fsp.get_member(member_id)
        achievements = await fsp.get_achievements(member_id)
        self.db.add(
            FspLink(
                candidate_user_id=user.id,
                fsp_member_id=member_id,
                sync_status=FspSyncStatus.synced.value,
                last_synced_at=self.now,
                raw_snapshot={
                    "member": member.model_dump(mode="json"),
                    "achievements": [a.model_dump(mode="json") for a in achievements],
                },
            )
        )
        self.db.add_all(
            FspAchievement(
                candidate_user_id=user.id,
                external_id=a.external_id,
                achievement_type=a.achievement_type,
                discipline=a.discipline,
                competition_name=a.competition_name,
                result=a.result,
                place=a.place,
                role=a.role,
                sport_rank=a.sport_rank,
                achieved_at=a.achieved_at,
            )
            for a in achievements
        )

    def vacancies(self) -> None:
        for seed in data.VACANCIES:
            company = self.companies[seed.employer]
            vacancy = Vacancy(
                id=uuid.uuid4(),
                company_id=company.id,
                company_name=company.name,
                title=seed.title,
                description=seed.description,
                specialization_id=self.specs[seed.specialization].id,
                grade_id=self.grades[seed.grade].id,
                salary_from=seed.salary_from,
                salary_to=seed.salary_to,
                work_format=seed.work_format,
                city=seed.city,
                status=seed.status.value,
                skills=[
                    *(
                        VacancySkill(skill=self.skills[s], required=True, weight=2)
                        for s in seed.required
                    ),
                    *(
                        VacancySkill(skill=self.skills[s], required=False, weight=1)
                        for s in seed.optional
                    ),
                ],
            )
            self.db.add(vacancy)
            self.vacancy_index[(seed.employer, seed.title)] = vacancy

    def _notify(self, user: User, kind: NotificationType, title: str, body: str, href: str) -> None:
        self.db.add(
            Notification(user_id=user.id, type=kind.value, title=title, body=body, href=href)
        )

    def offers(self) -> None:
        for seed in data.OFFERS:
            vacancy = self.vacancy_index[(seed.employer, seed.vacancy)] if seed.vacancy else None
            employer, candidate = self.users[seed.employer], self.users[seed.candidate]
            company = self.companies[seed.employer]
            responded = seed.status in {OfferStatus.accepted, OfferStatus.declined}
            offer = Offer(
                id=uuid.uuid4(),
                employer_user_id=employer.id,
                candidate_user_id=candidate.id,
                company_id=company.id,
                vacancy_id=vacancy.id if vacancy else None,
                company_name=company.name,
                position_title=seed.position_title,
                message=f"Приглашаем обсудить позицию «{seed.position_title}». "
                "Зарплата и формат указаны в предложении.",
                salary_from=seed.salary_from,
                salary_to=seed.salary_to,
                work_format=seed.work_format,
                employer_contact={"type": "email", "value": seed.employer},
                status=seed.status.value,
                viewed_at=self.now if seed.status != OfferStatus.new else None,
                responded_at=self.now if responded else None,
            )
            self.db.add(offer)
            self._notify(
                candidate,
                NotificationType.offer_new,
                "Новое предложение",
                f"{company.name}: {seed.position_title}",
                f"/candidate/offers/{offer.id}",
            )
            if responded:
                accepted = seed.status == OfferStatus.accepted
                self._notify(
                    employer,
                    NotificationType.offer_accepted
                    if accepted
                    else NotificationType.offer_declined,
                    "Оффер принят" if accepted else "Оффер отклонён",
                    f"{seed.position_title} · {candidate.display_name}",
                    f"/employer/candidates/{candidate.id}" if accepted else "/employer/offers",
                )

    def engagement(self) -> None:
        for employer_email, candidate_emails in data.SHORTLIST.items():
            employer = self.users[employer_email]
            for email in candidate_emails:
                candidate_id = self.users[email].id
                self.db.add(
                    ShortlistItem(employer_user_id=employer.id, candidate_user_id=candidate_id)
                )
                self.db.add(
                    ProfileView(candidate_user_id=candidate_id, employer_user_id=employer.id)
                )
        for email, vacancy_keys in data.SAVED_VACANCIES.items():
            for key in vacancy_keys:
                self.db.add(
                    SavedVacancy(
                        candidate_user_id=self.users[email].id,
                        vacancy_id=self.vacancy_index[key].id,
                    )
                )
        for email, vacancy_keys in data.APPLICATIONS.items():
            candidate = self.users[email]
            for employer_email, title in vacancy_keys:
                self.db.add(
                    Application(
                        candidate_user_id=candidate.id,
                        vacancy_id=self.vacancy_index[(employer_email, title)].id,
                    )
                )
                self._notify(
                    self.users[employer_email],
                    NotificationType.application,
                    "Новый отклик",
                    f"{candidate.display_name} откликнулся на «{title}»",
                    f"/employer/candidates/{candidate.id}",
                )


async def seed() -> None:
    async with SessionLocal() as db:
        if (await db.execute(select(Specialization.id).limit(1))).first():
            print("SEED_SKIP already seeded")
            return

        seeder = _Seeder(db)
        seeder.taxonomy()
        seeder.employers()
        await db.flush()  # users and taxonomy first: everything below references them
        seeder.questions()
        seeder.candidates()
        seeder.vacancies()
        await db.flush()
        await seeder.after_profiles()
        seeder.offers()
        seeder.engagement()
        await db.commit()
    print(
        f"SEED_OK accounts={len(seeder.users)} vacancies={len(seeder.vacancy_index)} "
        f"password={data.DEMO_PASSWORD}"
    )


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
