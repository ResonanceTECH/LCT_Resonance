"""ML-08 / ML-09: vacancy ranking + within-category scores.

`/rank` scores the candidate batch Backend already filtered (Talent Pool).
Retrieval from the resume catalog lives in `app.online`.
"""

from __future__ import annotations

from app.matcher import match_resume
from app.reranker import rerank
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
from app.scoring import MODEL_VERSION, category_label, category_score


def match_one(candidate: MatcherCandidate, vacancy: MatcherVacancy) -> MatcherMatch:
    return match_resume(candidate, vacancy).match


def rank(request: MatchingRequest) -> MatchingResponse:
    pairs = [match_resume(candidate, request.vacancy) for candidate in request.candidates]
    return MatchingResponse(matches=rerank(pairs), model_version=MODEL_VERSION)


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
