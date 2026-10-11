import pytest

from app.ranking import rank, rank_within_categories
from app.schemas import (
    CategoryRankRequest,
    MatcherCandidate,
    MatcherFspAchievement,
    MatcherVacancy,
    MatchingRequest,
)
from app.scoring import skill_match


VACANCY = MatcherVacancy(
    id="7",
    specialization="Frontend",
    required_grade="junior",
    required_skills=["React", "TypeScript", "Redux", "Git"],
    nice_to_have_skills=[],
    salary_from=170000,
    salary_to=220000,
    work_format="remote",
)


def candidate(**overrides) -> MatcherCandidate:
    base = {
        "id": "15",
        "specialization": "Frontend",
        "confirmed_grade": "junior",
        "declared_grade": "Junior",
        "test_score": 82,
        "skills": ["React", "TypeScript", "Git", "Python"],
        "experience_months": 10,
        "salary_from": 150000,
        "work_formats": ["remote"],
        "fsp_achievements": [
            MatcherFspAchievement(
                id="f1",
                title="Кубок",
                discipline="Программирование продуктовое",
                place_or_result="2 место",
                sport_rank="1 разряд",
                verified=True,
                achievement_type="prize",
            )
        ],
    }
    base.update(overrides)
    return MatcherCandidate(**base)


def test_skill_match_wording_and_normalization():
    score, matched, missing = skill_match(
        ["React.js", "TS", "Git"], ["React", "TypeScript", "Redux", "Git"], []
    )
    assert matched == ["React", "TypeScript", "Git"]
    assert missing == ["Redux"]
    assert score == pytest.approx(75.0)


def test_match_contract_shape_and_explanation():
    resp = rank(MatchingRequest(vacancy=VACANCY, candidates=[candidate()]))
    m = resp.matches[0]
    assert resp.model_version == "ml-v1"
    assert m.matched_skills == ["React", "TypeScript", "Git"]
    assert m.missing_in_profile_skills == ["Redux"]
    assert m.salary_compatible is True
    assert m.work_format_compatible is True
    assert m.grade_status == "confirmed"
    assert m.category is not None
    codes = {r.code for r in m.reasons}
    assert "SPECIALIZATION_MATCH" in codes
    assert "SKILLS_REQUIRED" in codes
    assert "FSP_VERIFIED" in codes
    assert m.components is not None
    assert m.score == pytest.approx(
        m.components.test + m.components.skills + m.components.fsp + m.components.conditions,
        abs=0.02,
    )
    assert 0 <= m.score <= 100


def test_empty_fsp_is_not_an_error():
    m = rank(
        MatchingRequest(vacancy=VACANCY, candidates=[candidate(fsp_achievements=[])])
    ).matches[0]
    assert m.components is not None
    assert m.components.fsp == 0
    assert "FSP_VERIFIED" not in {r.code for r in m.reasons}
    assert m.score > 0


def test_unverified_fsp_ignored():
    m = rank(
        MatchingRequest(
            vacancy=VACANCY,
            candidates=[
                candidate(
                    fsp_achievements=[
                        MatcherFspAchievement(
                            id="x", title="x", verified=False, achievement_type="prize"
                        )
                    ]
                )
            ],
        )
    ).matches[0]
    assert m.components.fsp == 0


def test_ranking_order_and_deterministic_ties():
    strong = candidate(id="a", test_score=90, skills=["React", "TypeScript", "Redux", "Git"])
    weak = candidate(id="b", test_score=60, skills=["React"])
    resp = rank(MatchingRequest(vacancy=VACANCY, candidates=[weak, strong]))
    assert [m.candidate_id for m in resp.matches] == ["a", "b"]

    t1 = candidate(id="b", test_score=80)
    t2 = candidate(id="a", test_score=80)
    resp = rank(MatchingRequest(vacancy=VACANCY, candidates=[t1, t2]))
    assert [m.candidate_id for m in resp.matches] == ["a", "b"]


def test_salary_mismatch_flagged_not_filtered():
    m = rank(
        MatchingRequest(vacancy=VACANCY, candidates=[candidate(salary_from=400000)])
    ).matches[0]
    assert m.salary_compatible is False
    assert any(r.code == "SALARY_MISMATCH" and not r.positive for r in m.reasons)


def test_outside_category_test_does_not_count():
    m = rank(
        MatchingRequest(
            vacancy=VACANCY, candidates=[candidate(confirmed_grade="middle", test_score=99)]
        )
    ).matches[0]
    assert m.components.test == 0


def test_category_rank():
    resp = rank_within_categories(
        CategoryRankRequest(
            candidates=[
                candidate(id="low", test_score=50, fsp_achievements=[]),
                candidate(id="high", test_score=95),
            ]
        )
    )
    assert resp.items[0].candidate_id == "high"
    assert resp.items[0].category_score >= resp.items[1].category_score


def test_demo_frontend_pair_anna_over_elena():
    """Same signal story as Backend demo: stack + FSP + conditions beat raw test."""
    vacancy = MatcherVacancy(
        id="v",
        specialization="Frontend",
        required_grade="middle",
        required_skills=["React", "TypeScript"],
        nice_to_have_skills=["Jest", "Vite"],
        salary_to=340000,
        work_format="remote",
    )
    anna = MatcherCandidate(
        id="anna",
        specialization="Frontend",
        confirmed_grade="middle",
        test_score=82,
        skills=["React", "TypeScript", "Vite"],
        salary_from=250000,
        work_format="remote",
        fsp_achievements=[
            MatcherFspAchievement(
                id="1",
                title="Кубок",
                discipline="Продуктовое программирование",
                achievement_type="prize",
                sport_rank="1 разряд",
                verified=True,
            )
        ],
    )
    elena = MatcherCandidate(
        id="elena",
        specialization="Frontend",
        confirmed_grade="middle",
        test_score=91,
        skills=["React", "JavaScript"],
        salary_from=240000,
        work_format="office",
    )
    resp = rank(MatchingRequest(vacancy=vacancy, candidates=[elena, anna]))
    assert [m.candidate_id for m in resp.matches] == ["anna", "elena"]
