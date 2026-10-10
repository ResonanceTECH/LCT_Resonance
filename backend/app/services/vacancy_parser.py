"""Draft vacancy from free text (POST /vacancies/parse, P2).

Deterministic rules, not an LLM: skills come from the skill dictionary (with synonyms),
everything else from keywords. The employer reviews the draft before saving it.
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.taxonomy import Skill
from app.schemas.vacancy import VacancyParseResult
from app.services.skills import normalize_skill_name

MIN_TEXT_LENGTH = 20

_SPECIALIZATION_KEYWORDS = [
    ("Fullstack", ("fullstack", "full-stack", "фулстек")),
    ("Mobile", ("mobile", "ios", "android", "kotlin", "swift", "мобильн")),
    ("DevOps", ("devops", "kubernetes", "terraform", "sre")),
    ("Data Science", ("data science", "machine learning", "ml-", "pandas", "data scientist")),
    ("QA", ("qa", "тестировщик", "selenium", "автотест")),
    ("Frontend", ("frontend", "фронтенд", "react", "vue", "angular")),
    ("Backend", ("backend", "бэкенд", "python", "golang", " go ", "java", "fastapi", "django")),
]
_GRADE_KEYWORDS = [
    ("lead", ("lead", "тимлид", "ведущ")),
    ("senior", ("senior", "сеньор", "старш")),
    ("junior", ("junior", "джун", "младш")),
    ("intern", ("intern", "стаж")),
    ("middle", ("middle", "мидл")),
]
_WORK_FORMATS = [
    ("remote", ("remote", "удал")),
    ("hybrid", ("hybrid", "гибрид")),
    ("office", ("office", "офис")),
]
_CITIES = ["Москва", "Санкт-Петербург", "Казань", "Екатеринбург", "Новосибирск", "Нижний Новгород"]
_NICE_TO_HAVE = re.compile(r"(будет плюсом|желательно|nice to have|плюсом будет)", re.IGNORECASE)
_SALARY_RANGE = re.compile(
    r"(\d[\d\s]{1,9})\s*(тыс|k|к)?\s*[–\-—до]+\s*(\d[\d\s]{1,9})\s*(тыс|k|к)?", re.IGNORECASE
)


def _first(lower: str, table: list[tuple[str, tuple[str, ...]]]) -> str | None:
    return next((value for value, words in table if any(w in lower for w in words)), None)


def _specialization(title: str, main: str) -> str | None:
    """Most keyword hits wins; the title counts triple. Optional skills are not counted."""
    title, main = f" {title.lower()} ", f" {main.lower()} "
    scores = {
        spec: 3 * sum(w in title for w in words) + sum(w in main for w in words)
        for spec, words in _SPECIALIZATION_KEYWORDS
    }
    best = max(scores, key=lambda spec: scores[spec])
    return best if scores[best] else None


def _amount(raw: str, thousands: bool) -> int:
    value = int(re.sub(r"\s", "", raw))
    return value * 1000 if thousands or value < 1000 else value


def _salary(text: str) -> tuple[int | None, int | None]:
    for match in _SALARY_RANGE.finditer(text):
        thousands = bool(match.group(2) or match.group(4))
        low, high = _amount(match.group(1), thousands), _amount(match.group(3), thousands)
        if 10_000 <= low <= high <= 10_000_000:
            return low, high
    return None, None


def _skill_mentions(text: str, skills: list[Skill]) -> list[str]:
    # "CI/CD" is one skill, "React/TypeScript" two: keep tokens both with and without "/".
    words = [t for t in re.split(r"[\s,;()]+", text) if t]
    tokens = {normalize_skill_name(w) for w in words}
    tokens |= {normalize_skill_name(part) for w in words for part in w.split("/") if part}
    found: list[str] = []
    for skill in skills:
        if {normalize_skill_name(skill.name), normalize_skill_name(skill.slug)} & tokens:
            found.append(skill.name)
    return found


async def parse(db: AsyncSession, text: str) -> VacancyParseResult:
    if len(text.strip()) < MIN_TEXT_LENGTH:
        raise AppError("TEXT_TOO_SHORT", "Слишком короткий текст вакансии", 400)
    lower = f" {text.lower()} "
    skills = list((await db.execute(select(Skill))).scalars().all())
    # Skills after "будет плюсом" and similar markers are optional.
    title = next((line.strip() for line in text.splitlines() if line.strip()), "")[:120]
    marker = _NICE_TO_HAVE.search(text)
    main, extra = (text[: marker.start()], text[marker.start() :]) if marker else (text, "")
    required = _skill_mentions(main, skills)
    optional = [s for s in _skill_mentions(extra, skills) if s not in required]
    salary_from, salary_to = _salary(text)
    return VacancyParseResult(
        title=title or None,
        description=text.strip()[:2000],
        specialization=_specialization(title, main),
        required_grade=_first(lower, _GRADE_KEYWORDS) or "middle",
        required_skills=required,
        nice_to_have_skills=optional,
        salary_from=salary_from,
        salary_to=salary_to,
        work_format=_first(lower, _WORK_FORMATS),
        # Stem match: "в Казани", "Москве".
        city=next((c for c in _CITIES if c.lower()[:-1] in lower), None),
    )
