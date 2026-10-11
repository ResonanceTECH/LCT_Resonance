import pytest

from app.integrations.matching.baseline import (
    FSP_SPORT_RANK_BONUS,
    BaselineMatcher,
    conditions_match,
    fsp_signal,
    skill_match,
)
from app.schemas.matcher_contract import (
    MatcherCandidate,
    MatcherFspAchievement,
    MatcherReason,
    MatcherVacancy,
    MatchingRequest,
)
from app.services.matching import render_reason

VACANCY = MatcherVacancy(
    id="vac-1",
    specialization="Backend",
    required_grade="middle",
    required_skills=["Python", "FastAPI"],
    nice_to_have_skills=["Docker"],
    salary_from=200000,
    salary_to=260000,
    work_format="remote",
)


def candidate(**overrides) -> MatcherCandidate:
    fields = {
        "id": "c",
        "specialization": "Backend",
        "confirmed_grade": "middle",
        "test_score": 80,
        "skills": ["Python", "FastAPI"],
        "salary_from": 200000,
        "work_format": "remote",
    }
    fields.update(overrides)
    return MatcherCandidate(**fields)


def achievement(type_: str = "participation", **overrides) -> MatcherFspAchievement:
    return MatcherFspAchievement(id="a", title="ФСП", achievement_type=type_, **overrides)


async def rank(*candidates: MatcherCandidate, vacancy: MatcherVacancy = VACANCY):
    return await BaselineMatcher().rank(
        MatchingRequest(vacancy=vacancy, candidates=list(candidates))
    )


def codes(match) -> dict[str, bool]:
    return {r.code: r.positive for r in match.reasons}


def test_contract_is_camel_case():
    payload = MatchingRequest(vacancy=VACANCY, candidates=[candidate()]).model_dump(by_alias=True)
    assert {"requiredGrade", "niceToHaveSkills", "salaryTo"} <= set(payload["vacancy"])
    assert {"confirmedGrade", "testScore", "fspAchievements"} <= set(payload["candidates"][0])


@pytest.mark.asyncio
async def test_skill_match_and_explainability():
    resp = await rank(
        candidate(
            id="a",
            test_score=86,
            skills=["Python", "FastAPI", "PostgreSQL"],
            fsp_achievements=[achievement("prize")],
        ),
        candidate(id="b", test_score=91, skills=["Python", "Django"]),
    )
    by_id = {m.candidate_id: m for m in resp.matches}
    assert by_id["a"].matched_skills == ["Python", "FastAPI"]
    assert by_id["b"].missing_in_profile_skills == ["FastAPI", "Docker"]
    assert codes(by_id["a"])["SKILLS_REQUIRED"] is True
    assert codes(by_id["b"])["SKILLS_REQUIRED"] is False
    assert codes(by_id["a"])["FSP_VERIFIED"] is True
    assert by_id["a"].components.fsp > 0 and by_id["b"].components.fsp == 0


@pytest.mark.asyncio
async def test_score_is_sum_of_weighted_components_and_bounded():
    match = (await rank(candidate(test_score=100, skills=["Python", "FastAPI", "Docker"]))).matches[
        0
    ]
    c = match.components
    assert match.score == pytest.approx(c.test + c.skills + c.fsp + c.conditions, abs=0.02)
    assert 0 <= match.score <= 100


@pytest.mark.asyncio
async def test_outside_category_test_does_not_count_and_is_explained():
    match = (await rank(candidate(confirmed_grade="junior"))).matches[0]
    assert match.components.test == 0
    assert codes(match)["GRADE_NOT_CONFIRMED"] is False


@pytest.mark.asyncio
async def test_salary_and_format_mismatch_are_explained_not_filtered():
    match = (await rank(candidate(salary_from=400000, work_format="office"))).matches[0]
    assert codes(match)["SALARY_MISMATCH"] is False
    assert codes(match)["WORK_FORMAT_MISMATCH"] is False
    assert match.components.conditions == 0


def test_sport_rank_bonus_counts_once():
    ranked = [achievement(sport_rank="1 разряд"), achievement(sport_rank="1 разряд")]
    assert fsp_signal(ranked) == 10 + 10 + FSP_SPORT_RANK_BONUS


def test_fsp_signal_is_capped_and_ignores_unverified():
    assert fsp_signal([achievement("prize")] * 10) == 100
    assert fsp_signal([achievement("prize", verified=False)]) == 0


def test_missing_condition_data_is_neutral():
    assert conditions_match(candidate(salary_from=None, work_format=None), VACANCY) == 50


def test_skill_match_normalizes_spelling_and_keeps_vacancy_spelling():
    score, matched, missing = skill_match(["React.js", "TS"], ["React", "TypeScript"], ["Jest"])
    assert matched == ["React", "TypeScript"]
    assert missing == ["Jest"]
    assert score == pytest.approx(100 * 4 / 5)


@pytest.mark.asyncio
async def test_ranking_combines_signals_not_only_test_score():
    """Backend.md demo pair: a weaker test but better stack/FSP/conditions ranks higher."""
    vacancy = MatcherVacancy(
        id="v",
        specialization="Frontend",
        required_grade="middle",
        required_skills=["React", "TypeScript"],
        nice_to_have_skills=["Jest", "Vite"],
        salary_to=340000,
        work_format="remote",
    )
    anna = candidate(
        id="anna",
        specialization="Frontend",
        test_score=82,
        skills=["React", "TypeScript", "Vite"],
        fsp_achievements=[achievement("prize", sport_rank="1 разряд")],
        salary_from=250000,
    )
    elena = candidate(
        id="elena",
        specialization="Frontend",
        test_score=91,
        skills=["React", "JavaScript"],
        salary_from=240000,
        work_format="office",
    )
    resp = await rank(elena, anna, vacancy=vacancy)
    assert [m.candidate_id for m in resp.matches] == ["anna", "elena"]


@pytest.mark.asyncio
async def test_ties_are_ordered_deterministically():
    resp = await rank(candidate(id="b"), candidate(id="a"))
    assert [m.candidate_id for m in resp.matches] == ["a", "b"]


def test_reason_labels_follow_backend_dictionary():
    assert render_reason(MatcherReason(code="TEST_SCORE", params={"score": 82})).label == (
        "результат теста 82/100"
    )
    mismatch = render_reason(
        MatcherReason(code="WORK_FORMAT_MISMATCH", params={"workFormat": "office"}, positive=False)
    )
    assert (mismatch.label, mismatch.positive) == ("формат кандидата: офис", False)
    assert render_reason(
        MatcherReason(code="SKILLS_OPTIONAL", params={"matched": 1, "total": 2})
    ).label == ("указаны 1 из 2 желательных навыков")
    # An ML model may send an unknown code or forget parameters: no crash, code as label.
    assert render_reason(MatcherReason(code="ML_CUSTOM")).label == "ML_CUSTOM"
    assert render_reason(MatcherReason(code="TEST_SCORE")).label == "TEST_SCORE"
