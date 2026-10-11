"""HTTP surface for the Resonance ML matcher.

Backend is the only product client and calls `POST /rank` (camelCase batch).
Catalog routes keep a mini-db of resumes and vacancies for offline indexing
and online content-filtered ranking. Frontend never talks to this service.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.categorize import categorize
from app.db.store import get_store
from app.grade import grade_status
from app.matcher import match_resume
from app.offline.build import rebuild_index
from app.online.pipeline import rank_resumes_for_vacancy, rank_vacancies_for_user, similar_resumes
from app.ranking import rank, rank_within_categories
from app.schemas import (
    CatalogWriteResponse,
    CategorizeRequest,
    CategorizeResponse,
    CategoryRankRequest,
    CategoryRankResponse,
    GradeStatusRequest,
    GradeStatusResponse,
    MatchPairRequest,
    MatcherCandidate,
    MatcherMatch,
    MatcherVacancy,
    MatchingRequest,
    MatchingResponse,
    NormalizeSkillsRequest,
    NormalizeSkillsResponse,
    OfflineRebuildResponse,
    OnlineResumeRankRequest,
    OnlineResumeRankResponse,
    OnlineVacancyRankRequest,
    OnlineVacancyRankResponse,
    ResumeCatalogResponse,
    SimilarResumesRequest,
    SimilarResumesResponse,
    VacancyCatalogResponse,
)
from app.scoring import MODEL_VERSION
from app.skills.normalize import normalize_skills


@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_store()
    yield


app = FastAPI(
    title="Resonance ML",
    version=__version__,
    description="Content-based vacancy/resume matcher, reranker, and explainable ranking.",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "modelVersion": MODEL_VERSION}


@app.post("/rank", response_model=MatchingResponse)
def post_rank(request: MatchingRequest) -> MatchingResponse:
    """Backend ↔ ML batch ranking (ML-05…ML-08, ML-10).

    Candidates are the Talent Pool batch. Score and order come from the matcher
    and reranker; this path does not read the mini-db.
    """
    return rank(request)


@app.post("/match", response_model=MatcherMatch)
def post_match(request: MatchPairRequest) -> MatcherMatch:
    """One vacancy ↔ resume pair."""
    return match_resume(request.candidate, request.vacancy).match


@app.post("/normalize-skills", response_model=NormalizeSkillsResponse)
def post_normalize(request: NormalizeSkillsRequest) -> NormalizeSkillsResponse:
    """ML-01."""
    return NormalizeSkillsResponse(skills=normalize_skills(request.skills))


@app.post("/categorize", response_model=CategorizeResponse)
def post_categorize(request: CategorizeRequest) -> CategorizeResponse:
    """ML-02: soft category. Talent Pool still uses the tested specialization and grade."""
    return categorize(request)


@app.post("/grade-status", response_model=GradeStatusResponse)
def post_grade_status(request: GradeStatusRequest) -> GradeStatusResponse:
    """ML-03: declared grade is never rewritten."""
    return grade_status(request)


@app.post("/category-rank", response_model=CategoryRankResponse)
def post_category_rank(request: CategoryRankRequest) -> CategoryRankResponse:
    """ML-09: ordering signal inside a specialization + grade category."""
    return rank_within_categories(request)


@app.put("/catalog/resumes", response_model=CatalogWriteResponse)
def put_resume(candidate: MatcherCandidate) -> CatalogWriteResponse:
    tokens = get_store().upsert_resume(candidate)
    return CatalogWriteResponse(id=candidate.id, indexed_tokens=tokens)


@app.get("/catalog/resumes", response_model=ResumeCatalogResponse)
def get_resumes() -> ResumeCatalogResponse:
    return ResumeCatalogResponse(items=get_store().list_resumes())


@app.put("/catalog/vacancies", response_model=CatalogWriteResponse)
def put_vacancy(vacancy: MatcherVacancy) -> CatalogWriteResponse:
    tokens = get_store().upsert_vacancy(vacancy)
    return CatalogWriteResponse(id=vacancy.id, indexed_tokens=tokens)


@app.get("/catalog/vacancies", response_model=VacancyCatalogResponse)
def get_vacancies() -> VacancyCatalogResponse:
    return VacancyCatalogResponse(items=get_store().list_vacancies())


@app.post("/offline/rebuild", response_model=OfflineRebuildResponse)
def post_offline_rebuild() -> OfflineRebuildResponse:
    """Recompute content vectors and the inverted index for every stored document."""
    return OfflineRebuildResponse(indexed=rebuild_index())


@app.post("/online/rank-resumes", response_model=OnlineResumeRankResponse)
def post_online_resumes(request: OnlineResumeRankRequest) -> OnlineResumeRankResponse:
    """Content-filter the resume catalog, then match and rerank for this vacancy."""
    return rank_resumes_for_vacancy(request.vacancy, request.limit)


@app.post("/online/rank-vacancies", response_model=OnlineVacancyRankResponse)
def post_online_vacancies(request: OnlineVacancyRankRequest) -> OnlineVacancyRankResponse:
    """Content-filter stored vacancies for this user resume, then match and rerank."""
    return rank_vacancies_for_user(request.candidate, request.limit)


@app.post("/online/similar-resumes", response_model=SimilarResumesResponse)
def post_similar_resumes(request: SimilarResumesRequest) -> SimilarResumesResponse:
    """Content filter: user profile against the resume database."""
    return similar_resumes(request.candidate, request.limit)
