"""Static data for `python -m app.seed`.

Reference data (specializations, grades, skills) is loaded on every stand. Everything
from the employers on is demo data for `--demo` only: the accounts match the frontend MSW
fixtures (`frontend/src/mocks/fixtures.ts`), and the password is for a demo stand only.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import OfferStatus, VacancyStatus

DEMO_PASSWORD = "demo1234"
DEMO_ADMIN_EMAIL = "admin@demo.ru"

SPECIALIZATIONS = [
    ("frontend", "Frontend"),
    ("backend", "Backend"),
    ("fullstack", "Fullstack"),
    ("mobile", "Mobile"),
    ("devops", "DevOps"),
    ("data-science", "Data Science"),
    ("qa", "QA"),
]

GRADES = [
    ("intern", 0, "Intern"),
    ("junior", 1, "Junior"),
    ("middle", 2, "Middle"),
    ("senior", 3, "Senior"),
    ("lead", 4, "Lead"),
]

SKILLS = [
    ("python", "Python"),
    ("fastapi", "FastAPI"),
    ("django", "Django"),
    ("postgresql", "PostgreSQL"),
    ("sql", "SQL"),
    ("redis", "Redis"),
    ("docker", "Docker"),
    ("kubernetes", "Kubernetes"),
    ("pytest", "Pytest"),
    ("golang", "Go"),
    ("java", "Java"),
    ("kotlin", "Kotlin"),
    ("swift", "Swift"),
    ("nodejs", "Node.js"),
    ("graphql", "GraphQL"),
    ("javascript", "JavaScript"),
    ("typescript", "TypeScript"),
    ("react", "React"),
    ("redux", "Redux"),
    ("css", "CSS"),
    ("vite", "Vite"),
    ("jest", "Jest"),
    ("git", "Git"),
    ("linux", "Linux"),
    ("ci-cd", "CI/CD"),
    ("terraform", "Terraform"),
    ("aws", "AWS"),
    ("ml", "Machine Learning"),
    ("pandas", "Pandas"),
    ("selenium", "Selenium"),
]

# Skill pools for the generated filler candidates.
SKILL_POOLS = {
    "backend": [
        "python",
        "fastapi",
        "django",
        "postgresql",
        "sql",
        "redis",
        "docker",
        "pytest",
        "git",
    ],
    "frontend": ["javascript", "typescript", "react", "redux", "css", "vite", "jest", "git"],
}


@dataclass(frozen=True)
class SeedEmployer:
    email: str
    display_name: str
    company_name: str
    description: str
    industry: str


EMPLOYERS = [
    SeedEmployer(
        "employer@demo.ru",
        "Игорь Смирнов",
        "Resonance Labs",
        "Развиваем продукт обратного рекрутинга",
        "HR-Tech",
    ),
    SeedEmployer(
        "employer2@demo.ru",
        "Ольга Петрова",
        "ТехноСфера",
        "Платёжные сервисы для малого бизнеса",
        "FinTech",
    ),
]


@dataclass(frozen=True)
class SeedCandidate:
    email: str
    full_name: str
    specialization: str
    # Grade confirmed by a test; None means the candidate has not been tested yet.
    grade: str | None
    test_score: int | None
    skills: tuple[str, ...]
    salary_from: int
    salary_to: int
    work_format: str
    city: str = "Москва"
    about: str = ""
    desired_position: str = ""
    experience_years: int = 3
    readiness: str = "open_to_offers"
    fsp_member_id: str | None = None


# A/B pairs show that ranking combines signals: Анна beats Елена on the React vacancy
# despite a lower test score (stack, FSP and conditions), Максим beats Денис likewise.
NAMED_CANDIDATES = [
    SeedCandidate(
        "candidate@demo.ru",
        "Анна Ковалёва",
        "frontend",
        "middle",
        82,
        ("react", "typescript", "css", "vite", "redux"),
        250000,
        320000,
        "remote",
        about="Frontend-разработчик с фокусом на React и доступность интерфейсов.",
        desired_position="Frontend Engineer",
        experience_years=4,
        fsp_member_id="FSP-2026-00123",
    ),
    SeedCandidate(
        "elena@demo.ru",
        "Елена Ветрова",
        "frontend",
        "middle",
        91,
        ("react", "javascript"),
        240000,
        280000,
        "office",
        city="Казань",
        about="Вёрстка и React, люблю продуктовые задачи.",
        desired_position="Frontend Developer",
        readiness="actively_looking",
    ),
    SeedCandidate(
        "maxim@demo.ru",
        "Максим Орлов",
        "backend",
        "middle",
        86,
        ("python", "fastapi", "postgresql", "docker"),
        230000,
        290000,
        "remote",
        city="Санкт-Петербург",
        about="Backend на Python, призёр соревнований ФСП.",
        desired_position="Backend Engineer",
        experience_years=5,
        readiness="actively_looking",
        fsp_member_id="FSP-2026-00456",
    ),
    SeedCandidate(
        "denis@demo.ru",
        "Денис Крылов",
        "backend",
        "middle",
        91,
        ("python", "django"),
        300000,
        360000,
        "hybrid",
        city="Екатеринбург",
        about="Django и высоконагруженные API.",
        desired_position="Python Developer",
        experience_years=6,
    ),
    SeedCandidate(
        "sofia@demo.ru",
        "София Белова",
        "backend",
        "middle",
        74,
        ("python", "fastapi", "redis"),
        210000,
        260000,
        "remote",
        about="Python backend, интеграции и очереди.",
        desired_position="Backend Developer",
        experience_years=2,
        fsp_member_id="FSP-2026-00789",
    ),
]

FILLER_NAMES = [
    "Павел Ильин",
    "Мария Соколова",
    "Артём Кузнецов",
    "Ольга Морозова",
    "Никита Волков",
    "Дарья Лебедева",
    "Егор Новиков",
    "Алина Фёдорова",
]
CITIES = ["Москва", "Санкт-Петербург", "Казань", "Новосибирск", "Екатеринбург"]


@dataclass(frozen=True)
class SeedVacancy:
    employer: str
    title: str
    description: str
    specialization: str
    grade: str
    salary_from: int
    salary_to: int
    work_format: str
    required: tuple[str, ...]
    optional: tuple[str, ...] = ()
    city: str | None = "Москва"
    status: VacancyStatus = VacancyStatus.active


VACANCIES = [
    SeedVacancy(
        "employer@demo.ru",
        "Frontend Engineer (React)",
        "Развиваем интерфейс платформы обратного рекрутинга.",
        "frontend",
        "middle",
        260000,
        340000,
        "remote",
        required=("react", "typescript"),
        optional=("jest", "vite"),
    ),
    SeedVacancy(
        "employer@demo.ru",
        "Backend Developer (Python)",
        "API подбора кандидатов и интеграция с ФСП.",
        "backend",
        "middle",
        200000,
        280000,
        "remote",
        required=("python", "fastapi"),
        optional=("docker", "postgresql"),
    ),
    SeedVacancy(
        "employer@demo.ru",
        "Junior Backend Developer",
        "Черновик потребности на стажировку в backend-команду.",
        "backend",
        "junior",
        120000,
        160000,
        "hybrid",
        required=("python", "sql"),
        status=VacancyStatus.draft,
    ),
    SeedVacancy(
        "employer2@demo.ru",
        "Python Backend Engineer",
        "Платёжный шлюз и биллинг.",
        "backend",
        "middle",
        220000,
        300000,
        "hybrid",
        required=("python", "postgresql"),
        optional=("redis",),
        city="Санкт-Петербург",
    ),
    SeedVacancy(
        "employer2@demo.ru",
        "Frontend Developer",
        "Личный кабинет клиента.",
        "frontend",
        "middle",
        200000,
        260000,
        "office",
        required=("react",),
        optional=("typescript",),
    ),
]


@dataclass(frozen=True)
class SeedOffer:
    employer: str
    candidate: str
    # Title of one of the employer's VACANCIES, or None for a direct offer.
    vacancy: str | None
    status: OfferStatus
    position_title: str
    salary_from: int
    salary_to: int
    work_format: str = "remote"


OFFERS = [
    SeedOffer(
        "employer@demo.ru",
        "maxim@demo.ru",
        "Backend Developer (Python)",
        OfferStatus.new,
        "Backend Developer (Python)",
        240000,
        280000,
    ),
    SeedOffer(
        "employer@demo.ru",
        "sofia@demo.ru",
        "Backend Developer (Python)",
        OfferStatus.viewed,
        "Backend Developer (Python)",
        210000,
        250000,
    ),
    SeedOffer(
        "employer@demo.ru",
        "denis@demo.ru",
        None,
        OfferStatus.accepted,
        "Senior-трек в backend",
        300000,
        340000,
        "hybrid",
    ),
    SeedOffer(
        "employer@demo.ru",
        "elena@demo.ru",
        "Frontend Engineer (React)",
        OfferStatus.declined,
        "Frontend Engineer (React)",
        260000,
        300000,
    ),
    SeedOffer(
        "employer2@demo.ru",
        "candidate@demo.ru",
        "Frontend Developer",
        OfferStatus.new,
        "Frontend Developer",
        220000,
        260000,
        "office",
    ),
]

# Employer -> candidates in the shortlist; candidate -> saved vacancy titles.
SHORTLIST = {"employer@demo.ru": ["maxim@demo.ru", "candidate@demo.ru"]}
SAVED_VACANCIES = {"candidate@demo.ru": [("employer2@demo.ru", "Frontend Developer")]}
# Candidate applications: they unlock contacts for the vacancy owner (ТЗ).
APPLICATIONS = {"sofia@demo.ru": [("employer2@demo.ru", "Python Backend Engineer")]}
