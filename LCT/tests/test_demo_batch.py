"""Прогон на демо-выборке: DoD из ML.md (пакетный /rank, пустой ФСП, порядок)."""

from __future__ import annotations

from app.categorize import categorize
from app.ranking import rank
from app.schemas import CategorizeRequest, MatchingRequest
from app.skills.normalize import normalize_skills
from tests.fixtures_demo import CANDIDATES, VACANCIES


def test_demo_pool_size():
    assert len(CANDIDATES) >= 15
    assert len(VACANCIES) >= 4


def test_normalize_skill_variants_on_demo_profiles():
    assert normalize_skills(["React.js", "TS", "Postgres", "Py"]) == [
        "React",
        "TypeScript",
        "PostgreSQL",
        "Python",
    ]


def test_rank_all_vacancies_returns_full_batch_and_bounded_scores():
    for vacancy in VACANCIES:
        # Talent Pool по вакансии: только своя подтверждённая категория.
        pool = [
            c
            for c in CANDIDATES
            if (c.specialization or "").casefold() == vacancy.specialization.casefold()
            and (c.confirmed_grade or "").casefold() == vacancy.required_grade.casefold()
        ]
        assert pool, f"empty pool for {vacancy.id}"
        resp = rank(MatchingRequest(vacancy=vacancy, candidates=pool))
        assert len(resp.matches) == len(pool)
        assert resp.model_version == "ml-v1"
        scores = [m.score for m in resp.matches]
        assert scores == sorted(scores, reverse=True)
        for m in resp.matches:
            assert 0 <= m.score <= 100
            assert m.reasons
            assert m.components is not None
            assert m.grade_status in {"confirmed", "not_confirmed", "unknown"}


def test_frontend_middle_anna_ranks_above_elena():
    vacancy = next(v for v in VACANCIES if v.id == "vac-fe-middle")
    pool = [c for c in CANDIDATES if c.id in {"anna", "elena", "no-fsp-fe", "salary-high", "weak-stack"}]
    resp = rank(MatchingRequest(vacancy=vacancy, candidates=pool))
    order = [m.candidate_id for m in resp.matches]
    assert order.index("anna") < order.index("elena")
    assert order.index("anna") < order.index("weak-stack")


def test_empty_and_unverified_fsp_do_not_break_ranking():
    vacancy = next(v for v in VACANCIES if v.id == "vac-fe-junior")
    pool = [c for c in CANDIDATES if c.id in {"maxim", "unverified-fsp"}]
    resp = rank(MatchingRequest(vacancy=vacancy, candidates=pool))
    by_id = {m.candidate_id: m for m in resp.matches}
    assert by_id["unverified-fsp"].components.fsp == 0
    assert by_id["maxim"].score > 0
    assert "FSP_VERIFIED" not in {r.code for r in by_id["unverified-fsp"].reasons}


def test_salary_mismatch_is_explained():
    vacancy = next(v for v in VACANCIES if v.id == "vac-fe-middle")
    cand = next(c for c in CANDIDATES if c.id == "salary-high")
    m = rank(MatchingRequest(vacancy=vacancy, candidates=[cand])).matches[0]
    assert m.salary_compatible is False
    assert any(r.code == "SALARY_MISMATCH" for r in m.reasons)


def test_optional_skills_reason_present():
    vacancy = next(v for v in VACANCIES if v.id == "vac-fe-middle")
    cand = next(c for c in CANDIDATES if c.id == "anna")
    m = rank(MatchingRequest(vacancy=vacancy, candidates=[cand])).matches[0]
    opt = next(r for r in m.reasons if r.code == "SKILLS_OPTIONAL")
    assert opt.params["matched"] >= 1
    assert opt.positive is True


def test_categorize_covers_demo_specializations():
    for cand in CANDIDATES:
        out = categorize(
            CategorizeRequest(
                candidate_id=cand.id,
                specialization=cand.specialization,
                skills=cand.skills,
                experience_months=cand.experience_months
                or (cand.experience_years * 12 if cand.experience_years else None),
                fsp_achievements=cand.fsp_achievements,
            )
        )
        assert out.category
        assert 0.0 <= out.confidence <= 1.0
