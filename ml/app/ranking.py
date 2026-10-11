"""ML-08 / ML-09: vacancy ranking + within-category scores."""

from __future__ import annotations

from app.reasons import build_reasons
from app.schemas import (
    CategoryRankItem,
    CategoryRankRequest,
    CategoryRankResponse,
    MatcherCandidate,
    MatcherMatch,
    MatcherVacancy,
    MatchingRequest,
    MatchingResponse,
)
from app.scoring import (
    MODEL_VERSION,
    category_label,
    category_score,
    resolve_grade_status,
    salary_fits,
    score_pair,
    work_format_fits,
)


def match_one(candidate: MatcherCandidate, vacancy: MatcherVacancy) -> MatcherMatch:
    score, components, matched, missing = score_pair(candidate, vacancy)
    return MatcherMatch(
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


def rank(request: MatchingRequest) -> MatchingResponse:
    matches = [match_one(c, request.vacancy) for c in request.candidates]
    matches.sort(
        key=lambda m: (
            -m.score,
            -(m.components.test if m.components else 0),
            -(m.category_score or 0),
            m.candidate_id,
        )
    )
    return MatchingResponse(matches=matches, model_version=MODEL_VERSION)


def rank_within_categories(request: CategoryRankRequest) -> CategoryRankResponse:
    items = [
        CategoryRankItem(
            category=category_label(c),
            candidate_id=c.id,
            category_score=category_score(c),
        )
        for c in request.candidates
    ]
    items.sort(key=lambda i: (-i.category_score, i.candidate_id))
    return CategoryRankResponse(items=items, model_version=MODEL_VERSION)
