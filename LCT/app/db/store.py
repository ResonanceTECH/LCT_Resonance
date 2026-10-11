"""Mini-DB: resumes, vacancies, and the offline content index."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from app.content import resume_vector, vacancy_vector
from app.schemas import MatcherCandidate, MatcherVacancy

SCHEMA = """
CREATE TABLE IF NOT EXISTS resumes (
    id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    vector_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vacancies (
    id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    vector_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS content_postings (
    doc_type TEXT NOT NULL CHECK (doc_type IN ('resume', 'vacancy')),
    doc_id TEXT NOT NULL,
    token TEXT NOT NULL,
    weight REAL NOT NULL,
    PRIMARY KEY (doc_type, doc_id, token)
);

CREATE INDEX IF NOT EXISTS ix_content_postings_token
    ON content_postings (token, doc_type);
"""

_store: "Store | None" = None


def _schema_sql() -> str:
    """Prefer the DDL file shipped next to this module; SCHEMA is the fallback."""
    path = Path(__file__).with_name("schema.sql")
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return SCHEMA


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_schema_sql())
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def upsert_resume(self, candidate: MatcherCandidate) -> int:
        vector = resume_vector(candidate)
        payload = candidate.model_dump(mode="json")
        with self._lock:
            self._write("resumes", candidate.id, payload, vector, "resume")
            self._conn.commit()
        return len(vector)

    def upsert_vacancy(self, vacancy: MatcherVacancy) -> int:
        vector = vacancy_vector(vacancy)
        payload = vacancy.model_dump(mode="json")
        with self._lock:
            self._write("vacancies", vacancy.id, payload, vector, "vacancy")
            self._conn.commit()
        return len(vector)

    def list_resumes(self) -> list[MatcherCandidate]:
        with self._lock:
            rows = self._conn.execute("SELECT payload_json FROM resumes ORDER BY id").fetchall()
        return [MatcherCandidate.model_validate(json.loads(row["payload_json"])) for row in rows]

    def list_vacancies(self) -> list[MatcherVacancy]:
        with self._lock:
            rows = self._conn.execute("SELECT payload_json FROM vacancies ORDER BY id").fetchall()
        return [MatcherVacancy.model_validate(json.loads(row["payload_json"])) for row in rows]

    def rebuild(self) -> int:
        """Offline pass: recompute every content vector and the inverted index."""
        with self._lock:
            resumes = self._conn.execute("SELECT payload_json FROM resumes").fetchall()
            vacancies = self._conn.execute("SELECT payload_json FROM vacancies").fetchall()
            self._conn.execute("DELETE FROM content_postings")
            count = 0
            for row in resumes:
                candidate = MatcherCandidate.model_validate(json.loads(row["payload_json"]))
                vector = resume_vector(candidate)
                self._write("resumes", candidate.id, candidate.model_dump(mode="json"), vector, "resume")
                count += 1
            for row in vacancies:
                vacancy = MatcherVacancy.model_validate(json.loads(row["payload_json"]))
                vector = vacancy_vector(vacancy)
                self._write("vacancies", vacancy.id, vacancy.model_dump(mode="json"), vector, "vacancy")
                count += 1
            self._conn.commit()
        return count

    def retrieve_resumes(
        self, query: dict[str, float], limit: int
    ) -> list[tuple[MatcherCandidate, float]]:
        return self._retrieve("resume", query, limit, MatcherCandidate)

    def retrieve_vacancies(
        self, query: dict[str, float], limit: int
    ) -> list[tuple[MatcherVacancy, float]]:
        return self._retrieve("vacancy", query, limit, MatcherVacancy)

    def _retrieve(self, doc_type: str, query: dict[str, float], limit: int, model: type):
        from app.content import cosine

        if not query or limit <= 0:
            return []
        tokens = list(query)
        placeholders = ",".join("?" * len(tokens))
        table = "resumes" if doc_type == "resume" else "vacancies"
        with self._lock:
            rows = self._conn.execute(
                f"""
                SELECT d.id, d.payload_json, d.vector_json
                FROM {table} AS d
                WHERE d.id IN (
                    SELECT DISTINCT doc_id
                    FROM content_postings
                    WHERE doc_type = ? AND token IN ({placeholders})
                )
                """,
                [doc_type, *tokens],
            ).fetchall()
        scored: list[tuple[object, float]] = []
        for row in rows:
            vector = json.loads(row["vector_json"])
            similarity = cosine(query, vector)
            if similarity <= 0:
                continue
            scored.append((model.model_validate(json.loads(row["payload_json"])), similarity))
        scored.sort(key=lambda item: (-item[1], item[0].id))  # type: ignore[attr-defined]
        return scored[:limit]

    def _write(
        self,
        table: str,
        doc_id: str,
        payload: dict,
        vector: dict[str, float],
        doc_type: str,
    ) -> None:
        self._conn.execute(
            f"""
            INSERT INTO {table} (id, payload_json, vector_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                payload_json = excluded.payload_json,
                vector_json = excluded.vector_json,
                updated_at = excluded.updated_at
            """,
            (doc_id, json.dumps(payload, ensure_ascii=False), json.dumps(vector), _now()),
        )
        self._conn.execute(
            "DELETE FROM content_postings WHERE doc_type = ? AND doc_id = ?",
            (doc_type, doc_id),
        )
        self._conn.executemany(
            """
            INSERT INTO content_postings (doc_type, doc_id, token, weight)
            VALUES (?, ?, ?, ?)
            """,
            [(doc_type, doc_id, token, weight) for token, weight in vector.items()],
        )


def get_store() -> Store:
    global _store
    if _store is None:
        path = os.environ.get("DATABASE_PATH", "data/resonance.db")
        _store = Store(path)
    return _store


def reset_store() -> None:
    """Drop the process-wide store. Tests use this to point at a temp file."""
    global _store
    if _store is not None:
        _store.close()
        _store = None
