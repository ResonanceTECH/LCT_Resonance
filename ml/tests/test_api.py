from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_rank_camel_case_roundtrip():
    payload = {
        "vacancy": {
            "id": "7",
            "specialization": "Frontend",
            "requiredGrade": "junior",
            "requiredSkills": ["React", "TypeScript", "Redux", "Git"],
            "niceToHaveSkills": [],
            "salaryFrom": 170000,
            "salaryTo": 220000,
            "workFormat": "remote",
        },
        "candidates": [
            {
                "id": "15",
                "specialization": "Frontend",
                "confirmedGrade": "junior",
                "testScore": 82,
                "skills": ["React", "TypeScript", "Git"],
                "salaryFrom": 150000,
                "workFormat": "remote",
                "fspAchievements": [],
            }
        ],
    }
    r = client.post("/rank", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "matches" in body and "modelVersion" in body
    m = body["matches"][0]
    assert m["candidateId"] == "15"
    assert "matchedSkills" in m
    assert "missingInProfileSkills" in m
    assert m["missingInProfileSkills"] == ["Redux"]


def test_normalize_and_categorize_endpoints():
    n = client.post("/normalize-skills", json={"skills": ["React.js", "Py"]})
    assert n.json()["skills"] == ["React", "Python"]

    c = client.post(
        "/categorize",
        json={"candidateId": 15, "specialization": "Frontend", "skills": ["React", "TS"]},
    )
    assert c.json()["category"] == "Frontend"
