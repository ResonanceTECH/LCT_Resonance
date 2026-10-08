import pytest

from app.integrations.matching.baseline import BaselineMatcher
from app.schemas.matcher_contract import (
    MatcherCandidate,
    MatcherCandidateAchievement,
    MatcherNeed,
    MatchingRequest,
)


@pytest.mark.asyncio
async def test_skill_match_and_explainability():
    matcher = BaselineMatcher()
    resp = await matcher.rank(
        MatchingRequest(
            need=MatcherNeed(
                specialization="backend",
                grade="middle",
                required_skills=["python", "fastapi"],
                optional_skills=["docker"],
                salary_to=260000,
                work_format="remote",
            ),
            candidates=[
                MatcherCandidate(
                    id="a",
                    verified_specialization="backend",
                    verified_grade="middle",
                    test_score=86,
                    skills=["python", "fastapi", "postgresql"],
                    fsp_achievements=[
                        MatcherCandidateAchievement(type="prize", discipline="algo", result="3")
                    ],
                    salary_min=190000,
                    work_format="remote",
                ),
                MatcherCandidate(
                    id="b",
                    verified_specialization="backend",
                    verified_grade="middle",
                    test_score=91,
                    skills=["python", "django"],
                    fsp_achievements=[],
                    salary_min=190000,
                    work_format="remote",
                ),
            ],
        )
    )
    assert len(resp.matches) == 2
    by_id = {m.candidate_id: m for m in resp.matches}
    assert "python" in by_id["a"].matched_skills
    assert "fastapi" in by_id["a"].matched_skills
    assert "fastapi" in by_id["b"].missing_skills
    assert "CATEGORY_MATCH" in by_id["a"].reason_codes
    assert by_id["a"].components.fsp > 0
    assert by_id["b"].components.fsp == 0


@pytest.mark.asyncio
async def test_match_total_formula_bounds():
    matcher = BaselineMatcher()
    resp = await matcher.rank(
        MatchingRequest(
            need=MatcherNeed(specialization="backend", grade="middle", required_skills=["python"]),
            candidates=[
                MatcherCandidate(
                    id="x",
                    verified_specialization="backend",
                    verified_grade="middle",
                    test_score=100,
                    skills=["python"],
                )
            ],
        )
    )
    assert resp.matches[0].score <= 100
    assert resp.matches[0].score >= 50
