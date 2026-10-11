-- Mini feature store for the vacancy ↔ resume matcher.
-- Flattened from the Backend tables the matcher actually reads:
--   candidate_profiles + candidate_skills + fsp_achievements  → resumes
--   vacancies + vacancy_skills                                → vacancies
-- Offline indexing writes content_postings (token → document).
-- Online retrieval uses that inverted index, then the matcher and reranker.

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
