"""Content vectors for vacancy ↔ resume filtering.

A document is a bag of tokens: specialization, grade, normalized skills,
work format, and verified FSP disciplines. Required vacancy skills weigh
more than profile skills and nice-to-have skills. Similarity is cosine.
"""

from __future__ import annotations

import math

from app.schemas import MatcherCandidate, MatcherVacancy
from app.skills.normalize import normalize_skill_key

SPEC_WEIGHT = 3.0
GRADE_WEIGHT = 1.0
PROFILE_SKILL_WEIGHT = 1.0
REQUIRED_SKILL_WEIGHT = 2.0
OPTIONAL_SKILL_WEIGHT = 1.0
FORMAT_WEIGHT = 1.0
FSP_WEIGHT = 1.0


def _add(vector: dict[str, float], token: str, weight: float) -> None:
    token = token.strip()
    if not token or weight == 0:
        return
    vector[token] = vector.get(token, 0.0) + weight


def resume_vector(candidate: MatcherCandidate) -> dict[str, float]:
    vector: dict[str, float] = {}
    if candidate.specialization:
        _add(vector, f"spec:{candidate.specialization.strip().casefold()}", SPEC_WEIGHT)
    grade = (candidate.confirmed_grade or candidate.declared_grade or "").strip().casefold()
    if grade:
        _add(vector, f"grade:{grade}", GRADE_WEIGHT)
    for skill in candidate.skills:
        key = normalize_skill_key(skill)
        if key:
            _add(vector, f"skill:{key}", PROFILE_SKILL_WEIGHT)
    formats = list(candidate.work_formats)
    if candidate.work_format:
        formats.append(candidate.work_format)
    for fmt in formats:
        _add(vector, f"fmt:{fmt.strip().casefold()}", FORMAT_WEIGHT)
    for achievement in candidate.fsp_achievements:
        if not achievement.verified or not achievement.discipline:
            continue
        _add(vector, f"fsp:{achievement.discipline.strip().casefold()}", FSP_WEIGHT)
    return vector


def vacancy_vector(vacancy: MatcherVacancy) -> dict[str, float]:
    vector: dict[str, float] = {}
    _add(vector, f"spec:{vacancy.specialization.strip().casefold()}", SPEC_WEIGHT)
    _add(vector, f"grade:{vacancy.required_grade.strip().casefold()}", GRADE_WEIGHT)
    for skill in vacancy.required_skills:
        key = normalize_skill_key(skill)
        if key:
            _add(vector, f"skill:{key}", REQUIRED_SKILL_WEIGHT)
    for skill in vacancy.nice_to_have_skills:
        key = normalize_skill_key(skill)
        if key:
            _add(vector, f"skill:{key}", OPTIONAL_SKILL_WEIGHT)
    if vacancy.work_format:
        _add(vector, f"fmt:{vacancy.work_format.strip().casefold()}", FORMAT_WEIGHT)
    return vector


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    """Cosine similarity in 0..1 for non-negative token weights."""
    if not left or not right:
        return 0.0
    dot = 0.0
    for token, weight in left.items():
        other = right.get(token)
        if other:
            dot += weight * other
    if dot <= 0:
        return 0.0
    left_norm = math.sqrt(sum(weight * weight for weight in left.values()))
    right_norm = math.sqrt(sum(weight * weight for weight in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
