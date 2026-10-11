"""Explainable baseline scoring (Backend.md, "Baseline matching").

score = 0.50 * test + 0.25 * skills + 0.15 * fsp + 0.10 * conditions, every part on 0..100.
The Talent Pool already filters by the verified category (specialization + grade), so the
category earns no points. Outside the category (e.g. "match to me" for a candidate of
another grade) the test result does not count and the mismatch is reported as a minus.
"""

from __future__ import annotations

from app.schemas.matcher_contract import (
    MatchComponents,
    MatcherCandidate,
    MatcherFspAchievement,
    MatcherMatch,
    MatcherReason,
    MatcherVacancy,
    MatchingRequest,
    MatchingResponse,
)
from app.services.skills import normalize_skill_name

MODEL_VERSION = "baseline-v1"

WEIGHTS = {"test": 0.50, "skills": 0.25, "fsp": 0.15, "conditions": 0.10}

REQUIRED_SKILL_WEIGHT = 2
OPTIONAL_SKILL_WEIGHT = 1

FSP_POINTS = {"participation": 10, "finalist": 20, "prize": 30}
# Added once per candidate, not per achievement.
FSP_SPORT_RANK_BONUS = 40
FSP_SIGNAL_CAP = 100

# Used when a condition cannot be evaluated (e.g. no salary expectation): 50, not 0.
NEUTRAL = 50.0
STRONG_TEST_SCORE = 70


class BaselineMatcher:
    name = "baseline"

    async def rank(self, request: MatchingRequest) -> MatchingResponse:
        matches = [_match(candidate, request.vacancy) for candidate in request.candidates]
        # Ties are broken by the test result, then by id, so the ranking is stable.
        matches.sort(
            key=lambda m: (-m.score, -(m.components.test if m.components else 0), m.candidate_id)
        )
        return MatchingResponse(matches=matches, model_version=MODEL_VERSION)


def in_category(candidate: MatcherCandidate, vacancy: MatcherVacancy) -> bool:
    return (
        candidate.specialization == vacancy.specialization
        and candidate.confirmed_grade == vacancy.required_grade
    )


def _match(candidate: MatcherCandidate, vacancy: MatcherVacancy) -> MatcherMatch:
    test = float(candidate.test_score or 0) if in_category(candidate, vacancy) else 0.0
    skills, matched, missing = skill_match(
        candidate.skills, vacancy.required_skills, vacancy.nice_to_have_skills
    )
    components = MatchComponents(
        test=round(WEIGHTS["test"] * test, 2),
        skills=round(WEIGHTS["skills"] * skills, 2),
        fsp=round(WEIGHTS["fsp"] * fsp_signal(candidate.fsp_achievements), 2),
        conditions=round(WEIGHTS["conditions"] * conditions_match(candidate, vacancy), 2),
    )
    score = components.test + components.skills + components.fsp + components.conditions
    return MatcherMatch(
        candidate_id=candidate.id,
        score=round(score, 2),
        matched_skills=matched,
        missing_in_profile_skills=missing,
        reasons=reasons(candidate, vacancy, matched),
        components=components,
    )


def skill_match(
    candidate_skills: list[str], required: list[str], optional: list[str]
) -> tuple[float, list[str], list[str]]:
    """Weighted share of the vacancy's skills listed in the profile.

    Returns (0..100, matched, missing) in the vacancy's spelling, so they display as is.
    """
    have = {normalize_skill_name(s) for s in candidate_skills}
    total = REQUIRED_SKILL_WEIGHT * len(required) + OPTIONAL_SKILL_WEIGHT * len(optional)
    if total == 0:
        return 100.0, [], []

    matched_weight = 0
    matched: list[str] = []
    missing: list[str] = []
    for skills, weight in ((required, REQUIRED_SKILL_WEIGHT), (optional, OPTIONAL_SKILL_WEIGHT)):
        for skill in skills:
            if normalize_skill_name(skill) in have:
                matched_weight += weight
                matched.append(skill)
            else:
                missing.append(skill)
    return 100.0 * matched_weight / total, matched, missing


def fsp_signal(achievements: list[MatcherFspAchievement]) -> float:
    # Unknown types from a future real FSP API count as plain participation.
    verified = [a for a in achievements if a.verified]
    points = sum(FSP_POINTS.get(a.achievement_type, FSP_POINTS["participation"]) for a in verified)
    if any(a.sport_rank for a in verified):
        points += FSP_SPORT_RANK_BONUS
    return float(min(FSP_SIGNAL_CAP, points))


def _work_format_fits(candidate: MatcherCandidate, vacancy: MatcherVacancy) -> bool | None:
    if not vacancy.work_format or not candidate.work_format:
        return None
    return candidate.work_format == vacancy.work_format


def _salary_fits(candidate: MatcherCandidate, vacancy: MatcherVacancy) -> bool | None:
    """The lower bound of the candidate's expectations against the vacancy's ceiling."""
    if vacancy.salary_to is None or candidate.salary_from is None:
        return None
    return candidate.salary_from <= vacancy.salary_to


def conditions_match(candidate: MatcherCandidate, vacancy: MatcherVacancy) -> float:
    def part(fits: bool | None) -> float:
        return NEUTRAL if fits is None else (100.0 if fits else 0.0)

    return 0.5 * part(_work_format_fits(candidate, vacancy)) + 0.5 * part(
        _salary_fits(candidate, vacancy)
    )


def relevant_achievements(
    achievements: list[MatcherFspAchievement], vacancy: MatcherVacancy
) -> list[MatcherFspAchievement]:
    """Achievements whose discipline or title mentions the specialization or a skill."""
    keys = {
        normalize_skill_name(s)
        for s in [vacancy.specialization, *vacancy.required_skills, *vacancy.nice_to_have_skills]
    }
    keys.discard("")

    def mentions(text: str | None) -> bool:
        words = {normalize_skill_name(w) for w in (text or "").replace("/", " ").split()}
        return bool(words & keys) or normalize_skill_name(text or "") in keys

    return [a for a in achievements if a.verified and (mentions(a.discipline) or mentions(a.title))]


def reasons(
    candidate: MatcherCandidate, vacancy: MatcherVacancy, matched: list[str]
) -> list[MatcherReason]:
    out: list[MatcherReason] = []
    if candidate.specialization == vacancy.specialization:
        out.append(
            MatcherReason(
                code="SPECIALIZATION_MATCH", params={"specialization": vacancy.specialization}
            )
        )
    else:
        out.append(
            MatcherReason(
                code="SPECIALIZATION_MISMATCH",
                params={"specialization": candidate.specialization or "не указана"},
                positive=False,
            )
        )
    if candidate.confirmed_grade == vacancy.required_grade:
        out.append(MatcherReason(code="GRADE_CONFIRMED", params={"grade": vacancy.required_grade}))
        if candidate.test_score is not None:
            out.append(
                MatcherReason(
                    code="TEST_SCORE",
                    params={"score": candidate.test_score},
                    positive=candidate.test_score >= STRONG_TEST_SCORE,
                )
            )
    else:
        out.append(
            MatcherReason(
                code="GRADE_NOT_CONFIRMED", params={"grade": vacancy.required_grade}, positive=False
            )
        )

    if vacancy.required_skills:
        required_matched = sum(1 for s in vacancy.required_skills if s in matched)
        out.append(
            MatcherReason(
                code="SKILLS_REQUIRED",
                params={"matched": required_matched, "total": len(vacancy.required_skills)},
                positive=required_matched == len(vacancy.required_skills),
            )
        )
    if vacancy.nice_to_have_skills:
        optional_matched = sum(1 for s in vacancy.nice_to_have_skills if s in matched)
        out.append(
            MatcherReason(
                code="SKILLS_OPTIONAL",
                params={"matched": optional_matched, "total": len(vacancy.nice_to_have_skills)},
                positive=optional_matched > 0,
            )
        )

    work_format_fits = _work_format_fits(candidate, vacancy)
    if work_format_fits is not None:
        out.append(
            MatcherReason(
                code="WORK_FORMAT_MATCH" if work_format_fits else "WORK_FORMAT_MISMATCH",
                params={
                    "workFormat": vacancy.work_format if work_format_fits else candidate.work_format
                },
                positive=work_format_fits,
            )
        )
    salary_fits = _salary_fits(candidate, vacancy)
    if salary_fits is not None:
        out.append(
            MatcherReason(
                code="SALARY_MATCH" if salary_fits else "SALARY_MISMATCH", positive=salary_fits
            )
        )

    verified = [a for a in candidate.fsp_achievements if a.verified]
    if verified:
        out.append(MatcherReason(code="FSP_VERIFIED", params={"count": len(verified)}))
    relevant = relevant_achievements(candidate.fsp_achievements, vacancy)
    if relevant:
        discipline = relevant[0].discipline or relevant[0].title
        out.append(MatcherReason(code="FSP_RELEVANT", params={"discipline": discipline}))
    return out
