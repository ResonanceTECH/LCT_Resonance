"""Online ranking over the mini-db.

1. Content filter — inverted index keeps documents that share tokens with the query.
2. Matcher — explainable vacancy ↔ resume score.
3. Reranker — contract order, with content similarity as a late tie-break.
"""

from __future__ import annotations

from app.content import resume_vector, vacancy_vector
from app.db.store import Store, get_store
from app.matcher import match_resume
from app.reranker import rerank
from app.schemas import (
    MatcherCandidate,
    MatcherVacancy,
    OnlineResumeRankResponse,
    OnlineVacancyRankResponse,
    SimilarResumesResponse,
    SimilarResume,
    VacancyMatch,
)
from app.scoring import MODEL_VERSION, category_label


def rank_resumes_for_vacancy(
    vacancy: MatcherVacancy,
    limit: int = 50,
    store: Store | None = None,
) -> OnlineResumeRankResponse:
    """Employer query: vacancy against the resume catalog."""
    target = store or get_store()
    shortlist = target.retrieve_resumes(vacancy_vector(vacancy), limit)
    pairs = [match_resume(candidate, vacancy) for candidate, _similarity in shortlist]
    # Retrieval cosine is recomputed inside the matcher from the same vectors.
    matches = rerank(pairs)
    return OnlineResumeRankResponse(
        matches=matches,
        model_version=MODEL_VERSION,
        retrieved=len(shortlist),
    )


def rank_vacancies_for_user(
    candidate: MatcherCandidate,
    limit: int = 20,
    store: Store | None = None,
) -> OnlineVacancyRankResponse:
    """Candidate query: user resume against stored vacancies."""
    target = store or get_store()
    shortlist = target.retrieve_vacancies(resume_vector(candidate), limit)
    items: list[VacancyMatch] = []
    for vacancy, similarity in shortlist:
        pair = match_resume(candidate, vacancy)
        items.append(
            VacancyMatch(
                vacancy_id=vacancy.id,
                score=pair.match.score,
                matched_skills=pair.match.matched_skills,
                missing_in_profile_skills=pair.match.missing_in_profile_skills,
                reasons=pair.match.reasons,
                components=pair.match.components,
                content_similarity=round(similarity, 4),
                salary_compatible=pair.match.salary_compatible,
                work_format_compatible=pair.match.work_format_compatible,
            )
        )
    items.sort(key=lambda item: (-item.score, -item.content_similarity, item.vacancy_id))
    return OnlineVacancyRankResponse(matches=items, model_version=MODEL_VERSION, retrieved=len(shortlist))


def similar_resumes(
    candidate: MatcherCandidate,
    limit: int = 10,
    store: Store | None = None,
) -> SimilarResumesResponse:
    """Content filter of the resume catalog against the user profile. Self is excluded."""
    target = store or get_store()
    shortlist = target.retrieve_resumes(resume_vector(candidate), limit + 1)
    items: list[SimilarResume] = []
    for other, similarity in shortlist:
        if other.id == candidate.id:
            continue
        items.append(
            SimilarResume(
                candidate_id=other.id,
                content_similarity=round(similarity, 4),
                category=category_label(other),
            )
        )
        if len(items) >= limit:
            break
    return SimilarResumesResponse(items=items, model_version=MODEL_VERSION)
