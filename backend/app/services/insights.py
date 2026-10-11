"""Skill radar and candidate comparison (P2); the public passport lives in `passport`.

The radar is an explainable estimate, not a per-skill exam: it starts from the grade
(confirmed by a test, otherwise the declared one minus a penalty), adds the test result,
the self-assessed skill level and FSP achievements that mention the skill.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.candidate import CandidateProfile
from app.models.user import User
from app.schemas.candidate import (
    CandidateCompareResponse,
    SkillMatrixRow,
    SkillRadar,
    SkillRadarAxis,
)
from app.services import profiles
from app.services.matching import MATCH_PROFILE_OPTIONS
from app.services.skills import normalize_skill_name

RADAR_AXES = 8
GRADE_BASE = {"intern": 35, "junior": 45, "middle": 60, "senior": 75, "lead": 85}
UNCONFIRMED_PENALTY = 10
COMPARE_MAX = 4


def skill_radar(profile: CandidateProfile) -> SkillRadar:
    confirmed = profiles.confirmed_grade(profile)
    if confirmed:
        base = GRADE_BASE[confirmed] + ((profile.last_test_score or 70) - 70) / 3
    else:
        declared = profile.declared_grade.code if profile.declared_grade else "junior"
        base = GRADE_BASE.get(declared, 45) - UNCONFIRMED_PENALTY
    fsp_text = " ".join(
        f"{a.discipline or ''} {a.competition_name or ''}"
        for a in profile.fsp_achievements
        if a.verified
    )
    fsp_words = {normalize_skill_name(w) for w in fsp_text.split()}
    axes = []
    for cs in profile.skills[:RADAR_AXES]:
        if cs.skill is None:
            continue
        score = base + (cs.level - 3) * 6
        if normalize_skill_name(cs.skill.name) in fsp_words:
            score += 5
        axes.append(SkillRadarAxis(skill=cs.skill.name, score=int(max(0, min(100, round(score))))))
    return SkillRadar(candidate_id=profile.user_id, axes=axes)


async def _load_visible(db: AsyncSession, candidate_ids: Sequence[UUID]) -> list[CandidateProfile]:
    rows = await db.execute(
        select(CandidateProfile)
        .join(User, User.id == CandidateProfile.user_id)
        .where(CandidateProfile.user_id.in_(candidate_ids), *profiles.visible_to_employers())
        .options(*MATCH_PROFILE_OPTIONS)
    )
    found = {p.user_id: p for p in rows.scalars().all()}
    return [found[cid] for cid in candidate_ids if cid in found]


async def radar_for(db: AsyncSession, candidate_id: UUID) -> SkillRadar:
    found = await _load_visible(db, [candidate_id])
    if not found:
        raise AppError("CANDIDATE_NOT_FOUND", "Кандидат не найден", 404)
    return skill_radar(found[0])


async def compare(db: AsyncSession, raw_ids: str) -> CandidateCompareResponse:
    try:
        ids = list(dict.fromkeys(UUID(part.strip()) for part in raw_ids.split(",") if part.strip()))
    except ValueError as exc:
        raise AppError("INVALID_IDS", "Некорректный список кандидатов", 400) from exc
    if len(ids) < 2:
        raise AppError("COMPARE_NEEDS_TWO", "Нужно минимум 2 кандидата", 400)
    if len(ids) > COMPARE_MAX:
        raise AppError(
            "COMPARE_TOO_MANY", f"Сравнить можно не больше {COMPARE_MAX} кандидатов", 400
        )
    candidates = await _load_visible(db, ids)
    radars = {p.user_id: skill_radar(p) for p in candidates}
    skills = list(dict.fromkeys(name for p in candidates for name in profiles.skill_names(p)))
    matrix = []
    for skill in skills:
        values: dict[str, int | None] = {}
        for p in candidates:
            axis = next((a for a in radars[p.user_id].axes if a.skill == skill), None)
            listed = skill in profiles.skill_names(p)
            # Listed beyond the radar's axes: a neutral 50 rather than "not listed".
            values[str(p.user_id)] = axis.score if axis else (50 if listed else None)
        matrix.append(SkillMatrixRow(skill=skill, values=values))
    return CandidateCompareResponse(
        candidates=await profiles.build_outs(db, candidates),
        skill_matrix=matrix,
        radars=list(radars.values()),
    )
