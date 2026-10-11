"""Reason codes stay inside the Backend dictionary (Backend.md, matching.REASON_LABELS)."""

from __future__ import annotations

from app.ranking import rank
from app.schemas import MatchingRequest
from tests.fixtures_demo import CANDIDATES, VACANCIES

BACKEND_REASON_CODES = {
    "SPECIALIZATION_MATCH",
    "SPECIALIZATION_MISMATCH",
    "GRADE_CONFIRMED",
    "GRADE_NOT_CONFIRMED",
    "TEST_SCORE",
    "SKILLS_REQUIRED",
    "SKILLS_OPTIONAL",
    "WORK_FORMAT_MATCH",
    "WORK_FORMAT_MISMATCH",
    "SALARY_MATCH",
    "SALARY_MISMATCH",
    "FSP_VERIFIED",
    "FSP_RELEVANT",
}


def test_every_reason_code_is_in_the_backend_dictionary():
    for vacancy in VACANCIES:
        response = rank(MatchingRequest(vacancy=vacancy, candidates=list(CANDIDATES)))
        assert response.model_version == "ml-v1"
        assert len(response.matches) == len(CANDIDATES)
        for match in response.matches:
            assert match.reasons
            for reason in match.reasons:
                assert reason.code in BACKEND_REASON_CODES
                assert isinstance(reason.positive, bool)
                assert isinstance(reason.params, dict)
