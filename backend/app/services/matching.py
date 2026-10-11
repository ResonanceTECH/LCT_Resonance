"""Scoring candidates against a vacancy through the configured matcher (ML or baseline).

The matcher returns reason codes with parameters; labels come from REASON_LABELS here, so
the baseline and an external ML model produce identical wording (Backend.md).
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from uuid import UUID

import httpx
from sqlalchemy.orm import selectinload

from app.integrations.matching import BaselineMatcher, get_matcher
from app.integrations.matching.baseline import FSP_POINTS, relevant_achievements
from app.models.candidate import CandidateProfile
from app.models.fsp import FspAchievement
from app.models.vacancy import Vacancy, VacancySkill
from app.schemas.candidate import CandidateMatch
from app.schemas.common import MatchReason
from app.schemas.matcher_contract import (
    MatcherCandidate,
    MatcherFspAchievement,
    MatcherReason,
    MatcherVacancy,
    MatchingRequest,
    MatchingResponse,
)
from app.services import profiles
from app.services.fsp import to_achievement_out

logger = logging.getLogger("app.matching")

VACANCY_OPTIONS = (
    selectinload(Vacancy.skills).selectinload(VacancySkill.skill),
    selectinload(Vacancy.specialization),
    selectinload(Vacancy.grade),
    selectinload(Vacancy.company),
)
MATCH_PROFILE_OPTIONS = (
    *profiles.PROFILE_OPTIONS,
    selectinload(CandidateProfile.fsp_achievements),
)
RELEVANT_FSP_LIMIT = 2

WORK_FORMAT_LABELS = {"remote": "удалённо", "hybrid": "гибрид", "office": "офис"}
# Backend.md, "Словарь причин". Codes are unique per list: the frontend uses them as keys.
REASON_LABELS = {
    "SPECIALIZATION_MATCH": "совпадает специализация {specialization}",
    "SPECIALIZATION_MISMATCH": "специализация кандидата: {specialization}",
    "GRADE_CONFIRMED": "грейд {grade} подтверждён тестом",
    "GRADE_NOT_CONFIRMED": "грейд {grade} не подтверждён тестом",
    "TEST_SCORE": "результат теста {score}/100",
    "SKILLS_REQUIRED": "указаны {matched} из {total} обязательных навыков",
    "SKILLS_OPTIONAL": "указаны {matched} из {total} желательных навыков",
    "WORK_FORMAT_MATCH": "подходит формат: {workFormat}",
    "WORK_FORMAT_MISMATCH": "формат кандидата: {workFormat}",
    "SALARY_MATCH": "ожидания кандидата в пределах вилки",
    "SALARY_MISMATCH": "ожидания кандидата выше вилки",
    "FSP_VERIFIED": "подтверждённые достижения ФСП: {count}",
    "FSP_RELEVANT": "достижение ФСП по дисциплине {discipline}",
}


def render_reason(reason: MatcherReason) -> MatchReason:
    params = dict(reason.params)
    if "workFormat" in params:
        params["workFormat"] = WORK_FORMAT_LABELS.get(params["workFormat"], params["workFormat"])
    template = REASON_LABELS.get(reason.code, reason.code)
    try:
        label = template.format(**params)
    except (KeyError, IndexError, ValueError):
        label = reason.code  # an ML model sent a code without the parameters it needs
    return MatchReason(code=reason.code, label=label, positive=reason.positive)


def matcher_vacancy(vacancy: Vacancy) -> MatcherVacancy:
    return MatcherVacancy(
        id=str(vacancy.id),
        specialization=vacancy.specialization.name,
        required_grade=vacancy.grade.code,
        required_skills=[s.skill.name for s in vacancy.skills if s.required],
        nice_to_have_skills=[s.skill.name for s in vacancy.skills if not s.required],
        salary_from=vacancy.salary_from,
        salary_to=vacancy.salary_to,
        work_format=vacancy.work_format,
    )


def _matcher_achievement(a: FspAchievement) -> MatcherFspAchievement:
    return MatcherFspAchievement(
        id=str(a.id),
        title=a.competition_name or a.discipline or "",
        discipline=a.discipline,
        place_or_result=a.result,
        sport_rank=a.sport_rank,
        verified=a.verified,
        achievement_type=a.achievement_type,
    )


def matcher_candidate(profile: CandidateProfile) -> MatcherCandidate:
    """The category is what the test confirmed; the declared one counts only before a test."""
    spec = profile.verified_specialization or profile.declared_specialization
    return MatcherCandidate(
        id=str(profile.user_id),
        specialization=spec.name if spec else None,
        confirmed_grade=profiles.confirmed_grade(profile),
        declared_grade=profile.declared_grade.code if profile.declared_grade else None,
        test_score=profile.last_test_score,
        skills=profiles.skill_names(profile),
        experience_years=profile.experience_years,
        salary_from=profile.salary_from,
        salary_to=profile.salary_to,
        work_format=profile.work_format,
        fsp_achievements=[_matcher_achievement(a) for a in profile.fsp_achievements if a.verified],
    )


def _relevant_fsp(profile: CandidateProfile, vacancy: MatcherVacancy) -> list[FspAchievement]:
    verified = [a for a in profile.fsp_achievements if a.verified]
    relevant_ids = {
        r.id for r in relevant_achievements([_matcher_achievement(a) for a in verified], vacancy)
    }
    # Relevant to the vacancy first, then the strongest results.
    verified.sort(
        key=lambda a: (str(a.id) not in relevant_ids, -FSP_POINTS.get(a.achievement_type, 0))
    )
    return verified[:RELEVANT_FSP_LIMIT]


async def _rank(request: MatchingRequest) -> tuple[MatchingResponse, str]:
    """Rank with the configured matcher; the demo must survive an ML outage."""
    matcher = get_matcher()
    if matcher.name != BaselineMatcher.name:
        try:
            return await matcher.rank(request), matcher.name
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("ml_matcher_failed_fallback_to_baseline", extra={"error": repr(exc)})
    baseline = BaselineMatcher()
    return await baseline.rank(request), baseline.name


async def match_profiles(
    vacancy: Vacancy, candidates: Sequence[CandidateProfile]
) -> dict[UUID, CandidateMatch]:
    """Matches keyed by candidate id, in ranking order. Profiles need MATCH_PROFILE_OPTIONS."""
    if not candidates:
        return {}
    mv = matcher_vacancy(vacancy)
    by_id = {str(p.user_id): p for p in candidates}
    response, _ = await _rank(
        MatchingRequest(vacancy=mv, candidates=[matcher_candidate(p) for p in candidates])
    )
    result: dict[UUID, CandidateMatch] = {}
    for match in response.matches:
        profile = by_id.get(match.candidate_id)
        if profile is None:  # an external matcher may echo unknown ids
            continue
        reasons = {r.code: render_reason(r) for r in match.reasons}  # unique codes
        result[profile.user_id] = CandidateMatch(
            candidate_id=profile.user_id,
            vacancy_id=vacancy.id,
            score=round(match.score),
            matched_skills=match.matched_skills,
            missing_in_profile_skills=match.missing_in_profile_skills,
            reasons=list(reasons.values()),
            relevant_fsp=[to_achievement_out(a) for a in _relevant_fsp(profile, mv)],
        )
    return result
