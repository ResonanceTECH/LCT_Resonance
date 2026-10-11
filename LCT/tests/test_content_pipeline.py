"""Content filter, mini-db, offline index, online matcher + reranker."""

from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from app.content import cosine, resume_vector, vacancy_vector
from app.db.store import SCHEMA, Store, reset_store
from app.main import app
from app.matcher import ScoredPair, match_resume
from app.offline.build import rebuild_index
from app.online.pipeline import rank_resumes_for_vacancy, rank_vacancies_for_user, similar_resumes
from app.reranker import rerank
from app.schemas import MatchComponents, MatcherCandidate, MatcherMatch, MatcherVacancy


FRONTEND = MatcherVacancy(
    id="vac-fe",
    specialization="Frontend",
    required_grade="middle",
    required_skills=["React", "TypeScript"],
    nice_to_have_skills=["Jest"],
    salary_from=200000,
    salary_to=300000,
    work_format="remote",
)

ANNA = MatcherCandidate(
    id="anna",
    specialization="Frontend",
    confirmed_grade="middle",
    declared_grade="middle",
    test_score=82,
    skills=["React.js", "TS", "Vite"],
    salary_from=250000,
    work_format="remote",
)

JAVA = MatcherCandidate(
    id="igor",
    specialization="Backend",
    confirmed_grade="senior",
    test_score=90,
    skills=["Java", "Spring"],
    salary_from=250000,
    work_format="office",
)


def test_content_similarity_prefers_overlapping_resume():
    close = cosine(resume_vector(ANNA), vacancy_vector(FRONTEND))
    far = cosine(resume_vector(JAVA), vacancy_vector(FRONTEND))
    assert close > far
    assert far == 0


def test_schema_file_matches_runtime_tables(tmp_path):
    from pathlib import Path

    schema_path = Path(__file__).resolve().parents[1] / "app" / "db" / "schema.sql"
    file_db = sqlite3.connect(tmp_path / "file.db")
    file_db.executescript(schema_path.read_text(encoding="utf-8"))
    code_db = sqlite3.connect(tmp_path / "code.db")
    code_db.executescript(SCHEMA)
    file_names = {
        row[0]
        for row in file_db.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'index')"
        )
    }
    code_names = {
        row[0]
        for row in code_db.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'index')"
        )
    }
    assert {"resumes", "vacancies", "content_postings", "ix_content_postings_token"} <= file_names
    assert file_names == code_names


def test_reranker_breaks_ties_by_content_then_id():
    def pair(candidate_id: str, similarity: float) -> ScoredPair:
        match = MatcherMatch(
            candidate_id=candidate_id,
            score=10,
            category_score=5,
            components=MatchComponents(test=4, skills=3, fsp=2, conditions=1),
        )
        return ScoredPair(match=match, content_similarity=similarity)

    by_content = rerank([pair("b", 0.2), pair("a", 0.9)])
    assert [item.candidate_id for item in by_content] == ["a", "b"]

    by_id = rerank([pair("b", 0.4), pair("a", 0.4)])
    assert [item.candidate_id for item in by_id] == ["a", "b"]


def test_offline_index_filters_resume_catalog(tmp_path):
    store = Store(tmp_path / "ml.db")
    store.upsert_resume(ANNA)
    store.upsert_resume(JAVA)
    store.upsert_vacancy(FRONTEND)
    assert rebuild_index(store) == 3

    ranked = rank_resumes_for_vacancy(FRONTEND, limit=10, store=store)
    assert ranked.retrieved == 1
    assert [item.candidate_id for item in ranked.matches] == ["anna"]
    assert ranked.model_version == "ml-v1"
    assert ranked.matches[0].matched_skills == ["React", "TypeScript"]
    assert "Jest" in ranked.matches[0].missing_in_profile_skills

    user = MatcherCandidate(
        id="user",
        specialization="Frontend",
        confirmed_grade="middle",
        skills=["React", "TypeScript"],
        work_format="remote",
        test_score=70,
    )
    vacancies = rank_vacancies_for_user(user, store=store)
    assert [item.vacancy_id for item in vacancies.matches] == ["vac-fe"]
    assert vacancies.matches[0].score > 0

    similar = similar_resumes(user, store=store)
    assert [item.candidate_id for item in similar.items] == ["anna"]
    assert similar.items[0].content_similarity > 0


def test_catalog_endpoints_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "api.db"))
    reset_store()
    client = TestClient(app)

    created = client.put(
        "/catalog/resumes",
        json={
            "id": "anna",
            "specialization": "Frontend",
            "confirmedGrade": "middle",
            "skills": ["React.js", "TS"],
            "testScore": 80,
            "workFormat": "remote",
        },
    )
    assert created.status_code == 200
    assert created.json()["indexedTokens"] > 0

    other = client.put(
        "/catalog/resumes",
        json={
            "id": "igor",
            "specialization": "Backend",
            "confirmedGrade": "senior",
            "skills": ["Java"],
            "testScore": 99,
        },
    )
    assert other.status_code == 200

    vacancy = client.put(
        "/catalog/vacancies",
        json={
            "id": "vac-fe",
            "specialization": "Frontend",
            "requiredGrade": "middle",
            "requiredSkills": ["React", "TypeScript"],
            "workFormat": "remote",
        },
    )
    assert vacancy.status_code == 200

    rebuilt = client.post("/offline/rebuild")
    assert rebuilt.status_code == 200
    assert rebuilt.json()["indexed"] == 3

    ranked = client.post(
        "/online/rank-resumes",
        json={
            "vacancy": {
                "id": "vac-fe",
                "specialization": "Frontend",
                "requiredGrade": "middle",
                "requiredSkills": ["React", "TypeScript"],
                "workFormat": "remote",
            }
        },
    )
    assert ranked.status_code == 200
    body = ranked.json()
    assert body["modelVersion"] == "ml-v1"
    assert [item["candidateId"] for item in body["matches"]] == ["anna"]

    listed = client.get("/catalog/resumes")
    assert {item["id"] for item in listed.json()["items"]} == {"anna", "igor"}


def test_match_endpoint_keeps_score_formula():
    client = TestClient(app)
    response = client.post(
        "/match",
        json={
            "vacancy": {
                "id": "7",
                "specialization": "Frontend",
                "requiredGrade": "junior",
                "requiredSkills": ["React", "TypeScript", "Redux", "Git"],
                "salaryTo": 220000,
                "workFormat": "remote",
            },
            "candidate": {
                "id": "15",
                "specialization": "Frontend",
                "confirmedGrade": "junior",
                "testScore": 82,
                "skills": ["React", "TypeScript", "Git"],
                "salaryFrom": 150000,
                "workFormat": "remote",
                "fspAchievements": [],
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    components = body["components"]
    assert body["score"] == round(
        components["test"] + components["skills"] + components["fsp"] + components["conditions"],
        2,
    )
    assert body["missingInProfileSkills"] == ["Redux"]
    pair = match_resume(
        MatcherCandidate(
            id="15",
            specialization="Frontend",
            confirmed_grade="junior",
            test_score=82,
            skills=["React", "TypeScript", "Git"],
            salary_from=150000,
            work_format="remote",
        ),
        MatcherVacancy(
            id="7",
            specialization="Frontend",
            required_grade="junior",
            required_skills=["React", "TypeScript", "Redux", "Git"],
            salary_to=220000,
            work_format="remote",
        ),
    )
    assert pair.content_similarity > 0
