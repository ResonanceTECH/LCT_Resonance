# Resonance ML

Explainable matching service for the hackathon MVP ([`ML.md`](../ML.md)).

Backend is the only client (`MATCHER_PROVIDER=ml`, `ML_MATCHER_URL`). Frontend never talks to ML.

## What it does (P0)

| Endpoint | Spec | Notes |
|----|----|----|
| `POST /rank` | ML-05…08, ML-10 | Backend ↔ ML batch contract (camelCase) |
| `POST /normalize-skills` | ML-01 | `React.js` → `React` |
| `POST /categorize` | ML-02 | Soft category; Talent Pool still uses tested category |
| `POST /grade-status` | ML-03 | Never auto-downgrades declared grade |
| `POST /category-rank` | ML-09 | Within-category ordering signal |
| `GET /health` | — | liveness |

## Scoring decision

Talent Pool hard-filters by specialization + confirmed grade (Backend.md), so `/rank` uses:

```text
0.50·test + 0.25·skills + 0.15·fsp + 0.10·conditions
```

ML.md’s 40/25/15/10/10 lives in `scoring.diagnostic_ml_spec_score` for soft / cross-category analysis — not as the primary Talent Pool score (avoids double-counting specialization).

Salary is a **compatibility flag**, not a prediction. Missing FSP is score 0 on that component, never an error.

## Run

```bash
cd ml
uv sync --group dev
uv run uvicorn app.main:app --reload --port 8001
uv run pytest
```

Docker: service `ml` in root `compose.yaml` (`:8001`). Point Backend at it:

```bash
MATCHER_PROVIDER=ml ML_MATCHER_URL=http://ml:8001 docker compose up -d --build
```

On ML outage Backend falls back to in-process `BaselineMatcher`.

## Demo batch

`tests/fixtures_demo.py` + `tests/test_demo_batch.py`: 15 кандидатов и 4 вакансии (прогон дня 3 из `ML.md`).

```bash
uv run pytest tests/test_demo_batch.py -q
```
