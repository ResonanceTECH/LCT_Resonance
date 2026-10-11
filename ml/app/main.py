"""HTTP surface for the Resonance ML matcher.

Backend is the only client. Contract: camelCase JSON, `POST /rank` batch ranking.
Extra endpoints cover ML-01…ML-04 / ML-09 for demos and Backend helpers.
"""

from __future__ import annotations

from fastapi import FastAPI

from app import __version__
from app.categorize import categorize
from app.grade import grade_status
from app.ranking import rank, rank_within_categories
from app.schemas import (
    CategorizeRequest,
    CategorizeResponse,
    CategoryRankRequest,
    CategoryRankResponse,
    GradeStatusRequest,
    GradeStatusResponse,
    MatchingRequest,
    MatchingResponse,
    NormalizeSkillsRequest,
    NormalizeSkillsResponse,
)
from app.scoring import MODEL_VERSION
from app.skills.normalize import normalize_skills

app = FastAPI(
    title="Resonance ML",
    version=__version__,
    description="Explainable matching, skill normalization, categorization.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "modelVersion": MODEL_VERSION}


@app.post("/rank", response_model=MatchingResponse)
def post_rank(request: MatchingRequest) -> MatchingResponse:
    """Backend ↔ ML batch ranking (ML-05…ML-08, ML-10)."""
    return rank(request)


@app.post("/normalize-skills", response_model=NormalizeSkillsResponse)
def post_normalize(request: NormalizeSkillsRequest) -> NormalizeSkillsResponse:
    """ML-01."""
    return NormalizeSkillsResponse(skills=normalize_skills(request.skills))


@app.post("/categorize", response_model=CategorizeResponse)
def post_categorize(request: CategorizeRequest) -> CategorizeResponse:
    """ML-02: мягкая подсказка категории. Talent Pool по-прежнему опирается на тест."""
    return categorize(request)


@app.post("/grade-status", response_model=GradeStatusResponse)
def post_grade_status(request: GradeStatusRequest) -> GradeStatusResponse:
    """ML-03: заявленный грейд не переписываем."""
    return grade_status(request)


@app.post("/category-rank", response_model=CategoryRankResponse)
def post_category_rank(request: CategoryRankRequest) -> CategoryRankResponse:
    """ML-09: сигнал порядка внутри категории."""
    return rank_within_categories(request)
