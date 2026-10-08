from __future__ import annotations

import asyncio
import random
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.company import Company
from app.models.enums import OfferStatus, VacancyStatus
from app.models.fsp import FspAchievement, FspLink
from app.models.offer import Offer
from app.models.taxonomy import Grade, Skill, Specialization
from app.models.testing import TestQuestion
from app.models.user import User
from app.models.vacancy import Vacancy, VacancySkill

SPECS = [
    ("frontend", "Frontend"),
    ("backend", "Backend"),
    ("data-ml", "Data / ML"),
    ("qa", "QA"),
    ("devops", "DevOps"),
    ("mobile", "Mobile"),
    ("algorithms", "Algorithms"),
]
GRADES = [("junior", 1, "Junior"), ("middle", 2, "Middle"), ("senior", 3, "Senior")]
SKILLS = [
    ("python", "Python"),
    ("fastapi", "FastAPI"),
    ("postgresql", "PostgreSQL"),
    ("django", "Django"),
    ("docker", "Docker"),
    ("react", "React"),
    ("typescript", "TypeScript"),
    ("kubernetes", "Kubernetes"),
    ("sql", "SQL"),
    ("redis", "Redis"),
    ("pytest", "Pytest"),
    ("git", "Git"),
    ("linux", "Linux"),
    ("aws", "AWS"),
    ("golang", "Go"),
    ("java", "Java"),
    ("kotlin", "Kotlin"),
    ("swift", "Swift"),
    ("ml", "Machine Learning"),
    ("pandas", "Pandas"),
    ("nodejs", "Node.js"),
    ("graphql", "GraphQL"),
    ("ci-cd", "CI/CD"),
    ("terraform", "Terraform"),
    ("selenium", "Selenium"),
]

TOPICS = ["http", "databases", "python", "algorithms", "architecture"]


async def seed() -> None:
    async with SessionLocal() as db:
        existing = (await db.execute(select(Specialization).limit(1))).scalar_one_or_none()
        if existing:
            print("SEED_SKIP already seeded")
            return

        specs: dict[str, Specialization] = {}
        for slug, name in SPECS:
            row = Specialization(id=uuid.uuid4(), slug=slug, name=name)
            db.add(row)
            specs[slug] = row

        grades: dict[str, Grade] = {}
        for code, rank, name in GRADES:
            row = Grade(id=uuid.uuid4(), code=code, rank=rank, name=name)
            db.add(row)
            grades[code] = row

        skills: dict[str, Skill] = {}
        for slug, name in SKILLS:
            row = Skill(id=uuid.uuid4(), slug=slug, name=name)
            db.add(row)
            skills[slug] = row
        await db.flush()

        # questions: 10+ per backend/middle topic pools
        for topic in TOPICS:
            for i in range(6):
                opts = [
                    {"id": "a", "text": f"{topic} option A {i}"},
                    {"id": "b", "text": f"{topic} option B {i}"},
                    {"id": "c", "text": f"{topic} option C {i}"},
                ]
                db.add(
                    TestQuestion(
                        id=uuid.uuid4(),
                        specialization_id=specs["backend"].id,
                        grade_id=grades["middle"].id,
                        topic=topic,
                        difficulty=2,
                        prompt=f"[{topic}] Demo question #{i+1}?",
                        options=opts,
                        correct_answer="b",
                    )
                )

        admin = User(
            id=uuid.uuid4(),
            email="admin@example.invalid",
            password_hash=hash_password("AdminPass123!"),
            role="admin",
            email_verified_at=datetime.now(UTC),
        )
        db.add(admin)

        # employers
        employers = []
        for i in range(2):
            u = User(
                id=uuid.uuid4(),
                email=f"employer{i+1}@example.invalid",
                password_hash=hash_password("EmployerPass123!"),
                role="employer",
                email_verified_at=datetime.now(UTC),
            )
            db.add(u)
            employers.append(u)
        await db.flush()

        companies = []
        for i, emp in enumerate(employers):
            c = Company(
                id=uuid.uuid4(),
                owner_user_id=emp.id,
                name=f"TechCompany {i+1}",
                description="Fintech product",
                industry="FinTech",
                website="https://example.invalid",
                contact_name="HR",
                contact_email=f"hr{i+1}@example.invalid",
            )
            db.add(c)
            companies.append(c)
        # third company for employer1
        companies.append(
            Company(
                id=uuid.uuid4(),
                owner_user_id=employers[0].id,
                name="Second Co",
                description="Second",
                contact_email="hr@example.invalid",
            )
        )
        db.add(companies[-1])
        await db.flush()

        vacancies = []
        for i in range(5):
            v = Vacancy(
                id=uuid.uuid4(),
                company_id=companies[i % len(companies)].id,
                title="Backend Developer",
                description="API development",
                specialization_id=specs["backend"].id,
                grade_id=grades["middle"].id,
                salary_from=200000,
                salary_to=260000,
                work_format="remote",
                status=VacancyStatus.published.value,
            )
            db.add(v)
            vacancies.append(v)
        await db.flush()
        for v in vacancies:
            for slug, required in [("python", True), ("fastapi", True), ("docker", False)]:
                db.add(
                    VacancySkill(
                        id=uuid.uuid4(),
                        vacancy_id=v.id,
                        skill_id=skills[slug].id,
                        required=required,
                        weight=2 if required else 1,
                    )
                )

        # Candidate A
        cand_a = User(
            id=uuid.uuid4(),
            email="candidate.a@example.invalid",
            password_hash=hash_password("CandidatePass123!"),
            role="candidate",
            email_verified_at=datetime.now(UTC),
        )
        db.add(cand_a)
        # Candidate B
        cand_b = User(
            id=uuid.uuid4(),
            email="candidate.b@example.invalid",
            password_hash=hash_password("CandidatePass123!"),
            role="candidate",
            email_verified_at=datetime.now(UTC),
        )
        db.add(cand_b)
        await db.flush()

        async def make_profile(
            user,
            first,
            last,
            score,
            skill_slugs,
            with_fsp: bool,
            *,
            fsp_member_id: str | None = None,
            fsp_external_id: str = "seed-prize",
        ):
            p = CandidateProfile(
                user_id=user.id,
                first_name=first,
                last_name=last,
                phone="+70000000000",
                telegram=f"@{first.lower()}_demo",
                city="Москва",
                experience_months=18,
                declared_specialization_id=specs["backend"].id,
                declared_grade_id=grades["middle"].id,
                verified_specialization_id=specs["backend"].id,
                verified_grade_id=grades["middle"].id,
                grade_verification_status="verified",
                salary_min=190000,
                work_format="remote",
                open_to_offers=True,
                last_test_score=score,
            )
            db.add(p)
            # FK targets on candidate_profiles — flush before skills/FSP
            await db.flush()
            for slug in skill_slugs:
                db.add(
                    CandidateSkill(
                        id=uuid.uuid4(),
                        candidate_user_id=user.id,
                        skill_id=skills[slug].id,
                        level=4,
                    )
                )
            if with_fsp:
                db.add(
                    FspLink(
                        candidate_user_id=user.id,
                        fsp_member_id=fsp_member_id or f"FSP-{user.id.hex[:12].upper()}",
                        sync_status="synced",
                    )
                )
                db.add(
                    FspAchievement(
                        id=uuid.uuid4(),
                        candidate_user_id=user.id,
                        external_id=fsp_external_id,
                        achievement_type="prize",
                        competition_name="Всероссийские соревнования",
                        discipline="Algorithms",
                        place=3,
                        verified=True,
                    )
                )
            await db.flush()
            return p

        await make_profile(
            cand_a,
            "Алексей",
            "К",
            86,
            ["python", "fastapi", "postgresql"],
            True,
            fsp_member_id="FSP-2026-00123",
        )
        await make_profile(cand_b, "Борис", "Д", 91, ["python", "django"], False)

        # more candidates, some without FSP
        for i in range(10):
            u = User(
                id=uuid.uuid4(),
                email=f"candidate{i+1}@example.invalid",
                password_hash=hash_password("CandidatePass123!"),
                role="candidate",
                email_verified_at=datetime.now(UTC),
            )
            db.add(u)
            await db.flush()
            await make_profile(
                u,
                f"Cand{i+1}",
                "X",
                random.randint(60, 95),
                random.sample(list(skills.keys()), 3),
                with_fsp=(i >= 5),
                fsp_member_id=f"FSP-SEED-{i+1:03d}" if i >= 5 else None,
                fsp_external_id=f"seed-{i}",
            )

        await db.flush()
        # sample offers
        for status in [
            OfferStatus.sent.value,
            OfferStatus.viewed.value,
            OfferStatus.accepted.value,
            OfferStatus.rejected.value,
        ]:
            db.add(
                Offer(
                    id=uuid.uuid4(),
                    employer_user_id=employers[0].id,
                    candidate_user_id=cand_a.id if status != OfferStatus.accepted.value else cand_b.id,
                    company_id=companies[0].id,
                    vacancy_id=vacancies[0].id if status != OfferStatus.sent.value else None,
                    title="Backend Developer",
                    description="Invite",
                    salary_from=220000,
                    salary_to=280000,
                    employer_contact={"type": "email", "value": "hr@example.invalid"},
                    status=status,
                )
            )

        await db.commit()
        print("SEED_OK")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
