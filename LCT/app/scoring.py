"""Explainable Match Score (ML-05…ML-07, ML-10).

Decision (hackathon, aligned with Backend.md):
  Talent Pool already hard-filters by specialization + confirmed grade, so we do **not**
  re-award specialization points inside `/rank`. Weights:

      50% test · 25% skills · 15% FSP · 10% conditions (salary + work format)

  ML.md's 40/25/15/10/10 is kept as `diagnostic_components()` for demos / jury slides
  when comparing soft matching without a hard category gate.
"""

from __future__ import annotations

from app.fsp_features import fsp_signal
from app.grade import grade_status
from app.schemas import (
    GradeStatusRequest,
    MatchComponents,
    MatcherCandidate,
    MatcherVacancy,
)
from app.skills.normalize import normalize_skill_key

MODEL_VERSION = "ml-v1"

WEIGHTS = {"test": 0.50, "skills": 0.25, "fsp": 0.15, "conditions": 0.10}
# ML.md exploratory weights (diagnostics only).
ML_SPEC_WEIGHTS = {
    "skills": 0.40,
    "specialization": 0.25,
    "test": 0.15,
    "fsp": 0.10,
    "preferences": 0.10,
}

REQUIRED_SKILL_WEIGHT = 2
OPTIONAL_SKILL_WEIGHT = 1
NEUTRAL = 50.0
STRONG_TEST_SCORE = 70
PASS_SCORE = 70


def in_category(candidate: MatcherCandidate, vacancy: MatcherVacancy) -> bool:
    return (
        (candidate.specialization or "").casefold() == vacancy.specialization.casefold()
        and (candidate.confirmed_grade or "").casefold() == vacancy.required_grade.casefold()
    )


def skill_match(
    candidate_skills: list[str], required: list[str], optional: list[str]
) -> tuple[float, list[str], list[str]]:
    """Weighted share of vacancy skills listed in the profile.

    Returns (0..100, matched, missing) using the **vacancy's spelling** for display.
    Missing means «не указан в профиле», not «не знает» (ML-06).
    """
    have = {normalize_skill_key(s) for s in candidate_skills}
    total = REQUIRED_SKILL_WEIGHT * len(required) + OPTIONAL_SKILL_WEIGHT * len(optional)
    if total == 0:
        return 100.0, [], []

    matched_weight = 0
    matched: list[str] = []
    missing: list[str] = []
    for skills, weight in ((required, REQUIRED_SKILL_WEIGHT), (optional, OPTIONAL_SKILL_WEIGHT)):
        for skill in skills:
            if normalize_skill_key(skill) in have:
                matched_weight += weight
                matched.append(skill)
            else:
                missing.append(skill)
    return 100.0 * matched_weight / total, matched, missing


def work_format_fits(candidate: MatcherCandidate, vacancy: MatcherVacancy) -> bool | None:
    formats = list(candidate.work_formats)
    if candidate.work_format:
        formats.append(candidate.work_format)
    formats = [f for f in formats if f]
    if not vacancy.work_format or not formats:
        return None
    return vacancy.work_format in formats


def salary_fits(candidate: MatcherCandidate, vacancy: MatcherVacancy) -> bool | None:
    """Candidate lower bound vs vacancy ceiling — compatibility flag, not a prediction."""
    if vacancy.salary_to is None or candidate.salary_from is None:
        return None
    return candidate.salary_from <= vacancy.salary_to


def conditions_match(candidate: MatcherCandidate, vacancy: MatcherVacancy) -> float:
    def part(fits: bool | None) -> float:
        return NEUTRAL if fits is None else (100.0 if fits else 0.0)

    return 0.5 * part(work_format_fits(candidate, vacancy)) + 0.5 * part(
        salary_fits(candidate, vacancy)
    )


def specialization_match(candidate: MatcherCandidate, vacancy: MatcherVacancy) -> float:
    if not candidate.specialization:
        return NEUTRAL
    return (
        100.0
        if candidate.specialization.casefold() == vacancy.specialization.casefold()
        else 0.0
    )


def resolve_grade_status(candidate: MatcherCandidate) -> str:
    declared = candidate.declared_grade or candidate.confirmed_grade or "unknown"
    if candidate.confirmed_grade:
        return "confirmed"
    return grade_status(
        GradeStatusRequest(declared_grade=declared, test_score=candidate.test_score, pass_score=PASS_SCORE)
    ).grade_status


_GRADE_DISPLAY = {
    "intern": "Intern",
    "junior": "Junior",
    "middle": "Middle",
    "senior": "Senior",
    "lead": "Lead",
}


def category_label(candidate: MatcherCandidate) -> str:
    spec = candidate.specialization or "Other"
    raw = (candidate.confirmed_grade or candidate.declared_grade or "?").strip()
    grade = _GRADE_DISPLAY.get(raw.casefold(), raw)
    return f"{spec} / {grade}"


def category_score(candidate: MatcherCandidate) -> float:
    """ML-09: within-category ranking signal (not shown as a public place number)."""
    test = float(candidate.test_score or 0)
    completeness = float(
        candidate.profile_completeness
        if candidate.profile_completeness is not None
        else _heuristic_completeness(candidate)
    )
    fsp = fsp_signal(candidate.fsp_achievements)
    skill_breadth = min(100.0, 12.0 * len(candidate.skills))
    return round(0.45 * test + 0.25 * completeness + 0.20 * fsp + 0.10 * skill_breadth, 2)


def _heuristic_completeness(candidate: MatcherCandidate) -> float:
    checks = [
        bool(candidate.specialization),
        bool(candidate.skills),
        candidate.test_score is not None,
        candidate.salary_from is not None or candidate.salary_to is not None,
        bool(candidate.work_format or candidate.work_formats),
        candidate.experience_years is not None or candidate.experience_months is not None,
        bool(candidate.fsp_achievements),
    ]
    return 100.0 * sum(checks) / len(checks)


def score_pair(
    candidate: MatcherCandidate, vacancy: MatcherVacancy
) -> tuple[float, MatchComponents, list[str], list[str]]:
    test_raw = float(candidate.test_score or 0) if in_category(candidate, vacancy) else 0.0
    skills_raw, matched, missing = skill_match(
        candidate.skills, vacancy.required_skills, vacancy.nice_to_have_skills
    )
    fsp_raw = fsp_signal(candidate.fsp_achievements, vacancy)
    cond_raw = conditions_match(candidate, vacancy)

    components = MatchComponents(
        test=round(WEIGHTS["test"] * test_raw, 2),
        skills=round(WEIGHTS["skills"] * skills_raw, 2),
        fsp=round(WEIGHTS["fsp"] * fsp_raw, 2),
        conditions=round(WEIGHTS["conditions"] * cond_raw, 2),
        specialization=round(ML_SPEC_WEIGHTS["specialization"] * specialization_match(candidate, vacancy), 2),
    )
    score = components.test + components.skills + components.fsp + components.conditions
    return round(score, 2), components, matched, missing


def diagnostic_ml_spec_score(candidate: MatcherCandidate, vacancy: MatcherVacancy) -> float:
    """ML.md soft formula — for analysis only, not returned as primary `score`."""
    skills_raw, _, _ = skill_match(
        candidate.skills, vacancy.required_skills, vacancy.nice_to_have_skills
    )
    test_raw = float(candidate.test_score or 0)
    fsp_raw = fsp_signal(candidate.fsp_achievements, vacancy)
    prefs = conditions_match(candidate, vacancy)
    return round(
        ML_SPEC_WEIGHTS["skills"] * skills_raw
        + ML_SPEC_WEIGHTS["specialization"] * specialization_match(candidate, vacancy)
        + ML_SPEC_WEIGHTS["test"] * test_raw
        + ML_SPEC_WEIGHTS["fsp"] * fsp_raw
        + ML_SPEC_WEIGHTS["preferences"] * prefs,
        2,
    )
