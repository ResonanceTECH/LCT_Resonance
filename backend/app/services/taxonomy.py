"""Taxonomy as the frontend sees it: specializations by name ("Frontend"), grades by code
("middle"), skills by display name with synonyms ("React.js" -> "React")."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.taxonomy import Grade, Skill, Specialization
from app.services.skills import normalize_skill_name


async def get_specialization(db: AsyncSession, specialization_id: UUID) -> Specialization:
    spec = await db.get(Specialization, specialization_id)
    if spec is None:
        raise AppError("TAXONOMY_NOT_FOUND", "Специализация не найдена", 404)
    return spec


async def get_grade(db: AsyncSession, grade_id: UUID) -> Grade:
    grade = await db.get(Grade, grade_id)
    if grade is None:
        raise AppError("TAXONOMY_NOT_FOUND", "Грейд не найден", 404)
    return grade


async def specialization_by_name(db: AsyncSession, name: str) -> Specialization:
    result = await db.execute(select(Specialization))
    wanted = name.strip().casefold()
    for spec in result.scalars().all():
        if wanted in (spec.name.casefold(), spec.slug.casefold()):
            return spec
    raise AppError(
        "UNKNOWN_SPECIALIZATION", f"Неизвестная специализация: {name}", 422, {"value": name}
    )


async def grade_by_code(db: AsyncSession, code: str) -> Grade:
    grade = (await db.execute(select(Grade).where(Grade.code == code))).scalar_one_or_none()
    if grade is None:
        raise AppError("UNKNOWN_GRADE", f"Неизвестный грейд: {code}", 422, {"value": code})
    return grade


def _dedupe(names: Iterable[str]) -> list[str]:
    seen: dict[str, str] = {}
    for name in names:
        clean = name.strip()
        key = normalize_skill_name(clean)
        if clean and key and key not in seen:
            seen[key] = clean
    return list(seen.values())


async def _skill_index(db: AsyncSession) -> dict[str, Skill]:
    skills = (await db.execute(select(Skill))).scalars().all()
    index: dict[str, Skill] = {}
    for skill in skills:
        index.setdefault(normalize_skill_name(skill.slug), skill)
        index.setdefault(normalize_skill_name(skill.name), skill)
    return index


async def resolve_skills(db: AsyncSession, names: Sequence[str]) -> list[Skill]:
    """Skills for the given names, matched through synonyms; unknown ones are created
    (Backend.md: an unknown skill joins the dictionary without synonyms)."""
    index = await _skill_index(db)
    result: list[Skill] = []
    for name in _dedupe(names):
        key = normalize_skill_name(name)
        skill = index.get(key)
        if skill is None:
            skill = Skill(slug=key[:64], name=name[:128])
            db.add(skill)
            index[key] = skill
        result.append(skill)
    return result


async def find_skills(db: AsyncSession, names: Sequence[str]) -> list[Skill] | None:
    """Existing skills for a search filter; None if any of them is unknown to the system."""
    index = await _skill_index(db)
    found = [index.get(normalize_skill_name(name)) for name in _dedupe(names)]
    return None if any(s is None for s in found) else [s for s in found if s is not None]


def like_pattern(query: str) -> str:
    """`%query%` with LIKE wildcards escaped; use with `.ilike(pattern, escape="\\\\")`."""
    escaped = query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
