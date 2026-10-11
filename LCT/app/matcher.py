"""Vacancy ↔ resume matcher.

The primary score stays the Talent Pool formula from ML.md / Backend.md:

    0.50·test + 0.25·skills + 0.15·fsp + 0.10·conditions

Content similarity is a separate retrieval signal. It is not added to `score`,
so Backend and the contract tests keep a single explainable number.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.content import cosine, resume_vector, vacancy_vector
from app.reasons import build_reasons
from app.schemas import MatcherCandidate, MatcherMatch, MatcherVacancy
from app.scoring import (
    category_label,
    category_score,
    resolve_grade_status,
    salary_fits,
    score_pair,
    work_format_fits,
)


@dataclass(frozen=True)
class ScoredPair:
    match: MatcherMatch
    content_similarity: float


def match_resume(candidate: MatcherCandidate, vacancy: MatcherVacancy) -> ScoredPair:
    score, components, matched, missing = score_pair(candidate, vacancy)
    match = MatcherMatch(
        candidate_id=candidate.id,
        score=score,
        matched_skills=matched,
        missing_in_profile_skills=missing,
        reasons=build_reasons(candidate, vacancy, matched),
        components=components,
        category=category_label(candidate),
        category_score=category_score(candidate),
        grade_status=resolve_grade_status(candidate),
        salary_compatible=salary_fits(candidate, vacancy),
        work_format_compatible=work_format_fits(candidate, vacancy),
    )
    similarity = cosine(resume_vector(candidate), vacancy_vector(vacancy))
    return ScoredPair(match=match, content_similarity=similarity)
